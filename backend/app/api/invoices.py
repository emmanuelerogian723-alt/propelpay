"""Invoices endpoints"""
import secrets
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
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
from app.services.email import send_invoice_notification, send_payment_received, send_payment_reminder
from app.services.ai import write_follow_up
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
    due_date: Optional[str] = None  # YYYY-MM-DD
    notes: Optional[str] = None
    terms: Optional[str] = None
    auto_reminders: bool = True

def _invoice_dict(inv: Invoice, items: list = None) -> dict:
    return {
        "id": inv.id, "invoice_number": inv.invoice_number, "title": inv.title,
        "client_id": inv.client_id, "subtotal": inv.subtotal,
        "tax_rate": inv.tax_rate, "tax_amount": inv.tax_amount,
        "discount": inv.discount, "total": inv.total,
        "currency": inv.currency, "status": inv.status,
        "due_date": inv.due_date, "paid_at": inv.paid_at,
        "public_token": inv.public_token, "paystack_payment_link": inv.paystack_payment_link,
        "notes": inv.notes, "terms": inv.terms,
        "auto_reminders": inv.auto_reminders, "reminder_count": inv.reminder_count,
        "created_at": str(inv.created_at),
        "items": [{"id": i.id, "description": i.description, "quantity": i.quantity,
                   "unit_price": i.unit_price, "total": i.total} for i in (items or [])]
    }

async def _gen_invoice_number(db: AsyncSession, user_id: str) -> str:
    count_result = await db.execute(
        select(func.count(Invoice.id)).where(Invoice.user_id == user_id)
    )
    count = count_result.scalar() or 0
    return f"INV-{date.today().strftime('%Y%m')}-{(count+1):04d}"

@router.get("")
async def list_invoices(status: Optional[str] = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    q = select(Invoice).where(Invoice.user_id == user.id)
    if status: q = q.where(Invoice.status == status)
    result = await db.execute(q.order_by(Invoice.created_at.desc()))
    return [_invoice_dict(i) for i in result.scalars().all()]

@router.post("")
async def create_invoice(body: InvoiceReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
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
        auto_reminders=body.auto_reminders, public_token=token, status="draft"
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
async def get_invoice(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    items_res = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == inv.id))
    return _invoice_dict(inv, items_res.scalars().all())

@router.post("/{invoice_id}/send")
async def send_invoice(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")

    client = None
    if inv.client_id:
        res = await db.execute(select(Client).where(Client.id == inv.client_id))
        client = res.scalar_one_or_none()

    # Generate Paystack payment link
    pay_url = f"{settings.FRONTEND_URL}/pay/{inv.public_token}"
    if client and settings.PAYSTACK_SECRET_KEY:
        cb = f"{settings.BACKEND_URL}/invoices/payment/verify/{inv.public_token}"
        link_result = await create_payment_link(
            email=client.email, amount=inv.total, currency=inv.currency,
            invoice_id=inv.id, invoice_number=inv.invoice_number,
            callback_url=cb, user_name=user.business_name or user.name
        )
        if link_result.get("authorization_url"):
            inv.paystack_payment_link = link_result["authorization_url"]
            pay_url = link_result["authorization_url"]

    inv.status = "sent"
    await db.commit()

    if client:
        amount_str = f"{inv.currency} {inv.total:,.2f}"
        asyncio.create_task(send_invoice_notification(
            client.email, client.name, user.business_name or user.name,
            inv.invoice_number, amount_str, inv.due_date or "N/A", pay_url
        ))

    return {"success": True, "payment_url": pay_url, "invoice_number": inv.invoice_number,
            "message": f"Invoice sent to {client.email if client else 'client'}"}

@router.post("/{invoice_id}/remind")
async def send_reminder(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Send AI-powered payment reminder."""
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status == "paid": raise HTTPException(400, "Invoice already paid")

    client = None
    if inv.client_id:
        res = await db.execute(select(Client).where(Client.id == inv.client_id))
        client = res.scalar_one_or_none()
    if not client: raise HTTPException(400, "No client attached to invoice")

    # Calculate overdue days
    days_overdue = 0
    if inv.due_date:
        due = datetime.strptime(inv.due_date, "%Y-%m-%d").date()
        days_overdue = max(0, (date.today() - due).days)

    inv.reminder_count += 1
    attempt = inv.reminder_count

    # AI-generated message
    ai_msg = write_follow_up(
        client_name=client.name, invoice_number=inv.invoice_number,
        amount=inv.total, currency=inv.currency, days_overdue=days_overdue,
        business_name=user.business_name or user.name, attempt=attempt
    )

    pay_url = inv.paystack_payment_link or f"{settings.FRONTEND_URL}/pay/{inv.public_token}"
    asyncio.create_task(send_payment_reminder(
        client.email, client.name, user.business_name or user.name,
        inv.invoice_number, f"{inv.currency} {inv.total:,.2f}",
        days_overdue, pay_url, ai_msg
    ))

    fu = FollowUp(invoice_id=inv.id, type="email", message=ai_msg, sent=True,
                  sent_at=datetime.utcnow().isoformat())
    db.add(fu)
    await db.commit()
    return {"success": True, "message": f"Reminder #{attempt} sent to {client.email}", "ai_message": ai_msg}

@router.post("/{invoice_id}/mark-paid")
async def mark_paid(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    inv.status = "paid"
    inv.paid_at = datetime.utcnow().isoformat()
    await db.commit()
    return {"success": True, "message": "Invoice marked as paid"}

@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    await db.delete(inv)
    await db.commit()
    return {"success": True}

# ── Public invoice view ────────────────────────────────────────────────────

@router.get("/public/{token}")
async def public_invoice(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.public_token == token))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status == "sent": inv.status = "viewed"; await db.commit()
    
    res = await db.execute(select(User).where(User.id == inv.user_id))
    sender = res.scalar_one_or_none()
    client = None
    if inv.client_id:
        cr = await db.execute(select(Client).where(Client.id == inv.client_id))
        client = cr.scalar_one_or_none()
    items_res = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == inv.id))

    return {
        **_invoice_dict(inv, items_res.scalars().all()),
        "sender": {"name": sender.name if sender else "", "business_name": sender.business_name if sender else "",
                   "email": sender.email if sender else "", "phone": sender.phone if sender else "",
                   "bank_name": sender.bank_name if sender else "",
                   "bank_account": sender.bank_account if sender else "",
                   "bank_account_name": sender.bank_account_name if sender else ""},
        "client": {"name": client.name if client else "", "email": client.email if client else "",
                   "company": client.company if client else ""},
        "payment_url": inv.paystack_payment_link or f"{settings.FRONTEND_URL}/pay/{token}"
    }

@router.get("/payment/verify/{token}")
async def verify_payment(token: str, reference: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.public_token == token))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")

    verify = await paystack_verify(reference)
    if verify.get("success"):
        inv.status = "paid"
        inv.paid_at = datetime.utcnow().isoformat()
        p = Payment(invoice_id=inv.id, user_id=inv.user_id, amount=verify["amount"],
                    currency=inv.currency, provider="paystack", reference=reference, status="success")
        db.add(p)
        await db.commit()
        res = await db.execute(select(User).where(User.id == inv.user_id))
        user = res.scalar_one_or_none()
        if user:
            asyncio.create_task(send_payment_received(
                user.email, user.business_name or user.name,
                f"{inv.currency} {inv.total:,.2f}", inv.invoice_number
            ))
        return {"success": True, "message": "Payment confirmed!", "invoice": inv.invoice_number}
    return {"success": False, "message": "Payment not verified"}
