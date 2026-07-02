"""Invoices endpoints — v2 with Resend email + email tracking"""
import secrets
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceItem
from app.models.client import Client
from app.models.payment import Payment
from app.models.follow_up import FollowUp
from app.services.auth import get_current_user
from app.services.payments import create_payment_link, paystack_verify
from app.services.email import (
    send_invoice_email, send_payment_received,
    send_payment_reminder as _send_reminder
)
from app.services.ai import write_follow_up
from app.services.pdf_generator import generate_invoice_pdf, generate_receipt_pdf
from app.config import get_settings
import asyncio

settings = get_settings()
router = APIRouter(prefix="/invoices", tags=["invoices"])


class ItemReq(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float

class InvoiceReq(BaseModel):
    client_id: Optional[str] = None
    title: Optional[str] = None
    items: List[ItemReq]
    tax_rate: float = 0
    discount: float = 0
    currency: str = "NGN"
    due_date: Optional[str] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    auto_reminders: bool = True
    late_fee_enabled: bool = False
    late_fee_percent: float = 0


def _invoice_dict(inv: Invoice, items: list = None, client: Client = None) -> dict:
    return {
        "id": inv.id, "invoice_number": inv.invoice_number, "title": inv.title,
        "client_id": inv.client_id,
        "client_name": client.name if client else None,
        "client_email": client.email if client else None,
        "subtotal": inv.subtotal, "tax_rate": inv.tax_rate, "tax_amount": inv.tax_amount,
        "discount": inv.discount, "total": inv.total,
        "currency": inv.currency, "status": inv.status,
        "due_date": inv.due_date, "paid_at": inv.paid_at,
        "public_token": inv.public_token,
        "paystack_payment_link": inv.paystack_payment_link,
        "notes": inv.notes, "terms": inv.terms,
        "auto_reminders": inv.auto_reminders, "reminder_count": inv.reminder_count,
        "reminder_stage": inv.reminder_stage,
        "late_fee_enabled": inv.late_fee_enabled, "late_fee_percent": inv.late_fee_percent,
        "late_fee_applied": inv.late_fee_applied,
        "created_at": str(inv.created_at),
        "items": [{"id": i.id, "description": i.description, "quantity": i.quantity,
                   "unit_price": i.unit_price, "total": i.total} for i in (items or [])]
    }


async def _gen_invoice_number(db: AsyncSession, user_id: str) -> str:
    count_result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.user_id == user_id))
    count = count_result.scalar() or 0
    return f"INV-{date.today().strftime('%Y%m')}-{(count+1):04d}"


async def _get_items(db: AsyncSession, invoice_id: str) -> list:
    res = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id))
    return res.scalars().all()


async def _get_client(db: AsyncSession, client_id: str) -> Optional[Client]:
    if not client_id: return None
    res = await db.execute(select(Client).where(Client.id == client_id))
    return res.scalar_one_or_none()


@router.get("")
async def list_invoices(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Invoice).where(Invoice.user_id == user.id)
    if status:
        q = q.where(Invoice.status == status)
    result = await db.execute(q.order_by(Invoice.created_at.desc()))
    invoices = result.scalars().all()
    # Batch load clients
    client_ids = list({i.client_id for i in invoices if i.client_id})
    clients = {}
    if client_ids:
        cr = await db.execute(select(Client).where(Client.id.in_(client_ids)))
        for c in cr.scalars().all():
            clients[c.id] = c
    return [_invoice_dict(i, client=clients.get(i.client_id)) for i in invoices]


@router.post("")
async def create_invoice(
    body: InvoiceReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    inv_number = await _gen_invoice_number(db, user.id)
    token = secrets.token_urlsafe(32)
    subtotal = sum(item.quantity * item.unit_price for item in body.items)
    tax_amount = subtotal * (body.tax_rate / 100)
    total = subtotal + tax_amount - body.discount
    due = body.due_date or (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

    inv = Invoice(
        user_id=user.id, client_id=body.client_id,
        invoice_number=inv_number, title=body.title,
        subtotal=subtotal, tax_rate=body.tax_rate, tax_amount=tax_amount,
        discount=body.discount, total=total, currency=body.currency,
        due_date=due, notes=body.notes, terms=body.terms,
        auto_reminders=body.auto_reminders, public_token=token, status="draft",
        late_fee_enabled=body.late_fee_enabled,
        late_fee_percent=body.late_fee_percent if body.late_fee_enabled else 0,
    )
    db.add(inv)
    await db.flush()
    items = []
    for item in body.items:
        ii = InvoiceItem(
            invoice_id=inv.id, description=item.description,
            quantity=item.quantity, unit_price=item.unit_price,
            total=item.quantity * item.unit_price
        )
        db.add(ii)
        items.append(ii)
    await db.commit()
    await db.refresh(inv)
    return _invoice_dict(inv, items)


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    items = await _get_items(db, inv.id)
    client = await _get_client(db, inv.client_id)
    return _invoice_dict(inv, items, client)


@router.put("/{invoice_id}")
async def update_invoice(
    invoice_id: str, data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    allowed = ["title", "notes", "terms", "due_date", "currency", "tax_rate", "discount",
               "auto_reminders", "late_fee_enabled", "late_fee_percent"]
    for k, v in data.items():
        if k in allowed: setattr(inv, k, v)
    await db.commit()
    return {"success": True}


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")

    client = await _get_client(db, inv.client_id)
    if not client: raise HTTPException(400, "Please attach a client to this invoice before sending")

    # Generate Paystack payment link
    # NOTE: create_payment_link() already converts naira -> kobo internally
    # (it does amount*100). Passing an already-multiplied value here used to
    # cause a DOUBLE conversion — a real ₦10,000 invoice was generating a
    # Paystack checkout for ₦100,000,000 (100x, then x100 again = 10,000x).
    # Fixed: pass the raw invoice total, let create_payment_link() do the
    # kobo conversion exactly once.
    pay_url = f"{settings.FRONTEND_URL}/pay/{inv.public_token}"
    if settings.PAYSTACK_SECRET_KEY:
        try:
            cb = f"{settings.BACKEND_URL}/invoices/payment/verify/{inv.public_token}"
            link_result = await create_payment_link(
                email=client.email, amount=inv.total,
                invoice_id=inv.id, invoice_number=inv.invoice_number,
                callback_url=cb, currency=inv.currency,
                user_name=user.business_name or user.name
            )
            if link_result.get("authorization_url"):
                inv.paystack_payment_link = link_result["authorization_url"]
                pay_url = link_result["authorization_url"]
        except Exception as e:
            pass  # Non-fatal, use fallback URL

    inv.status = "sent"
    await db.commit()

    # NOTE: this used to call send_invoice_email() with kwargs that didn't
    # match its real signature (sender_name/invoice_number/amount/items/pay_url
    # instead of user_name/inv_number/total/pay_link) — that raised a TypeError
    # *synchronously* (argument binding happens before create_task can wrap it),
    # crashing this entire endpoint with a 500 on every single "Send Invoice"
    # click, even though the DB had already committed status="sent" just above.
    asyncio.create_task(send_invoice_email(
        to=client.email,
        client_name=client.name,
        inv_number=inv.invoice_number,
        total=inv.total,
        currency=inv.currency,
        due_date=inv.due_date or "N/A",
        pay_link=pay_url,
        user_name=user.business_name or user.name,
        user_id=user.id,
        invoice_id=inv.id
    ))

    return {
        "success": True,
        "payment_url": pay_url,
        "invoice_number": inv.invoice_number,
        "message": f"Invoice sent to {client.email}",
        "email_provider": "resend" if settings.RESEND_API_KEY else ("smtp" if settings.SMTP_USER else "none")
    }


@router.post("/{invoice_id}/remind")
async def send_reminder(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status == "paid": raise HTTPException(400, "Invoice already paid")
    client = await _get_client(db, inv.client_id)
    if not client: raise HTTPException(400, "No client attached to invoice")

    days_overdue = 0
    if inv.due_date:
        due = datetime.strptime(inv.due_date, "%Y-%m-%d").date()
        days_overdue = max(0, (date.today() - due).days)

    inv.reminder_count = (inv.reminder_count or 0) + 1

    ai_msg = write_follow_up(
        client_name=client.name, invoice_number=inv.invoice_number,
        amount=inv.total, currency=inv.currency,
        days_overdue=days_overdue,
        business_name=user.business_name or user.name,
        attempt=inv.reminder_count
    )

    pay_url = inv.paystack_payment_link or f"{settings.FRONTEND_URL}/pay/{inv.public_token}"

    asyncio.create_task(_send_reminder(
        to=client.email, client_name=client.name,
        business_name=user.business_name or user.name,
        invoice_number=inv.invoice_number,
        amount=f"{inv.currency} {inv.total:,.2f}",
        days_overdue=days_overdue, pay_url=pay_url,
        custom_message=ai_msg,
        user_id=user.id, invoice_id=inv.id
    ))

    fu = FollowUp(invoice_id=inv.id, type="email", message=ai_msg,
                  sent=True, sent_at=datetime.utcnow().isoformat())
    db.add(fu)
    await db.commit()
    return {
        "success": True,
        "message": f"Reminder #{inv.reminder_count} sent to {client.email}",
        "ai_message": ai_msg
    }


@router.post("/{invoice_id}/mark-paid")
async def mark_paid(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    inv.status = "paid"
    inv.paid_at = datetime.utcnow().isoformat()
    await db.commit()

    # Notify business owner
    if user.email:
        asyncio.create_task(send_payment_received(
            to=user.email, business_name=user.business_name or user.name,
            amount=f"{inv.currency} {inv.total:,.2f}",
            invoice_number=inv.invoice_number,
            user_id=user.id, invoice_id=inv.id
        ))
    return {"success": True, "message": "Invoice marked as paid"}


@router.delete("/{invoice_id}")
async def delete_invoice(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    await db.delete(inv)
    await db.commit()
    return {"success": True}


# ── PDF endpoints ─────────────────────────────────────────────────────────────

@router.get("/{invoice_id}/pdf")
async def get_pdf(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from fastapi.responses import Response
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    items = await _get_items(db, inv.id)
    client = await _get_client(db, inv.client_id)
    item_dicts = [{"description": i.description, "quantity": i.quantity,
                   "unit_price": i.unit_price, "total": i.total} for i in items]
    pdf_bytes = generate_invoice_pdf(
        invoice_number=inv.invoice_number,
        business_name=user.business_name or user.name or "My Business",
        business_email=user.email,
        client_name=client.name if client else "Client",
        client_email=client.email if client else "",
        items=item_dicts,
        subtotal=inv.subtotal, tax_rate=inv.tax_rate, tax_amount=inv.tax_amount,
        discount=inv.discount, total=inv.total, currency=inv.currency,
        due_date=str(inv.due_date or ""), created_date=str(inv.created_at)[:10],
        notes=inv.notes, terms=inv.terms, status=inv.status,
        paystack_link=inv.paystack_payment_link
    )
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{inv.invoice_number}.pdf"',
                             "Access-Control-Expose-Headers": "Content-Disposition"})


@router.get("/{invoice_id}/receipt")
async def get_receipt(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from fastapi.responses import Response
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status != "paid": raise HTTPException(400, "Invoice is not paid yet")
    items = await _get_items(db, inv.id)
    client = await _get_client(db, inv.client_id)
    pay_res = await db.execute(select(Payment).where(Payment.invoice_id == inv.id).order_by(Payment.created_at.desc()))
    payment = pay_res.scalars().first()
    tx_ref = payment.reference if payment else None
    pdf_bytes = generate_receipt_pdf(
        invoice_number=inv.invoice_number,
        business_name=user.business_name or user.name or "My Business",
        business_email=user.email,
        client_name=client.name if client else "Client",
        client_email=client.email if client else "",
        total=inv.total, currency=inv.currency,
        paid_at=str(inv.paid_at or ""),
        transaction_ref=tx_ref
    )
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="Receipt-{inv.invoice_number}.pdf"',
                             "Access-Control-Expose-Headers": "Content-Disposition"})


# ── Public invoice view ───────────────────────────────────────────────────────

@router.get("/public/{token}")
async def public_invoice(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.public_token == token))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status == "sent":
        inv.status = "viewed"
        await db.commit()
    res = await db.execute(select(User).where(User.id == inv.user_id))
    sender = res.scalar_one_or_none()
    client = await _get_client(db, inv.client_id)
    items = await _get_items(db, inv.id)
    return {
        **_invoice_dict(inv, items, client),
        "sender": {
            "name": sender.name if sender else "Business",
            "business_name": sender.business_name if sender else "",
            "email": sender.email if sender else "",
            "phone": sender.phone if sender else "",
        }
    }


# ── Paystack webhook ──────────────────────────────────────────────────────────

@router.post("/payment/verify/{token}", include_in_schema=False)
async def paystack_webhook(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Called by Paystack when payment is confirmed."""
    import hmac, hashlib
    body = await request.body()
    sig = request.headers.get("x-paystack-signature", "")
    if settings.PAYSTACK_SECRET_KEY:
        expected = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()
        if sig and sig != expected:
            raise HTTPException(400, "Invalid signature")

    result = await db.execute(select(Invoice).where(Invoice.public_token == token))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")

    try:
        data = await request.json()
        event = data.get("event", "")
        charge = data.get("data", {})
        if event == "charge.success" or charge.get("status") == "success":
            inv.status = "paid"
            inv.paid_at = datetime.utcnow().isoformat()
            ref = charge.get("reference", "")
            payment = Payment(
                invoice_id=inv.id, user_id=inv.user_id,
                amount=inv.total, currency=inv.currency,
                provider="paystack", reference=ref, status="paid"
            )
            db.add(payment)
            await db.commit()
            # Notify business owner
            res = await db.execute(select(User).where(User.id == inv.user_id))
            owner = res.scalar_one_or_none()
            if owner:
                asyncio.create_task(send_payment_received(
                    to=owner.email, business_name=owner.business_name or owner.name,
                    amount=f"{inv.currency} {inv.total:,.2f}",
                    invoice_number=inv.invoice_number,
                    user_id=owner.id, invoice_id=inv.id
                ))
    except Exception as e:
        pass
    return {"status": "ok"}


# ── Email log for this invoice ─────────────────────────────────────────────────

@router.get("/{invoice_id}/emails")
async def invoice_emails(
    invoice_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get email delivery history for an invoice."""
    from app.models.email_log import EmailLog
    from sqlalchemy import select as sel
    result = await db.execute(sel(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    if not result.scalar_one_or_none(): raise HTTPException(404, "Invoice not found")
    logs = await db.execute(sel(EmailLog).where(EmailLog.invoice_id == invoice_id)
                             .order_by(EmailLog.created_at.desc()))
    return [{"id": l.id, "to": l.to_email, "subject": l.subject,
             "type": l.email_type, "status": l.status, "provider": l.provider,
             "sent_at": str(l.created_at)} for l in logs.scalars().all()]
