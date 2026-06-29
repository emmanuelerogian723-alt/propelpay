"""Recurring / Retainer Invoice API"""
import secrets, json
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice, InvoiceItem
from app.models.client import Client
from app.models.recurring_invoice import RecurringInvoice
from app.services.auth import get_current_user
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/recurring", tags=["recurring"])

FREQ_DAYS = {"weekly": 7, "monthly": 30, "quarterly": 91, "yearly": 365}

class ItemReq(BaseModel):
    description: str
    quantity: float = 1
    unit_price: float

class RecurringReq(BaseModel):
    client_id: Optional[str] = None
    title: str
    items: List[ItemReq]
    tax_rate: float = 0
    discount: float = 0
    currency: str = "NGN"
    notes: Optional[str] = None
    terms: Optional[str] = None
    frequency: str = "monthly"   # weekly/monthly/quarterly/yearly
    start_date: str               # YYYY-MM-DD
    end_date: Optional[str] = None
    auto_send: bool = True


def _rd(r: RecurringInvoice, client_name: str = None) -> dict:
    items = json.loads(r.items_json) if r.items_json else []
    subtotal = sum(float(i.get("unit_price",0)) * float(i.get("quantity",1)) for i in items)
    return {
        "id": r.id, "title": r.title, "client_id": r.client_id,
        "client_name": client_name, "currency": r.currency,
        "frequency": r.frequency, "start_date": r.start_date,
        "end_date": r.end_date, "next_run_date": r.next_run_date,
        "auto_send": r.auto_send, "status": r.status,
        "invoices_generated": r.invoices_generated,
        "subtotal": subtotal, "tax_rate": r.tax_rate,
        "total": subtotal + subtotal*(r.tax_rate/100) - r.discount,
        "items": items, "notes": r.notes,
        "created_at": str(r.created_at)
    }


def _next_date(from_date: str, frequency: str) -> str:
    d = date.fromisoformat(from_date)
    if frequency == "weekly":   d += timedelta(days=7)
    elif frequency == "monthly":
        month = d.month + 1
        year  = d.year + (month > 12)
        month = month if month <= 12 else month - 12
        import calendar
        last_day = calendar.monthrange(year, month)[1]
        d = d.replace(year=year, month=month, day=min(d.day, last_day))
    elif frequency == "quarterly": d += timedelta(days=91)
    elif frequency == "yearly":    d = d.replace(year=d.year+1)
    return d.isoformat()


async def _gen_invoice_number(db, user_id: str) -> str:
    count_res = await db.execute(select(func.count(Invoice.id)).where(Invoice.user_id == user_id))
    count = count_res.scalar() or 0
    return f"INV-{date.today().strftime('%Y%m')}-{(count+1):04d}"


async def _fire_invoice(rec: RecurringInvoice, db: AsyncSession) -> Invoice:
    """Generate one invoice from a recurring template."""
    items_data = json.loads(rec.items_json) if rec.items_json else []
    subtotal = sum(float(i.get("unit_price",0))*float(i.get("quantity",1)) for i in items_data)
    tax_amount = subtotal * (rec.tax_rate / 100)
    total = subtotal + tax_amount - rec.discount
    due = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")
    inv_number = await _gen_invoice_number(db, rec.user_id)
    token = secrets.token_urlsafe(32)

    inv = Invoice(
        user_id=rec.user_id, client_id=rec.client_id,
        invoice_number=inv_number, title=rec.title,
        subtotal=subtotal, tax_rate=rec.tax_rate, tax_amount=tax_amount,
        discount=rec.discount, total=total, currency=rec.currency,
        due_date=due, notes=rec.notes, terms=rec.terms,
        auto_reminders=True, public_token=token,
        status="draft"
    )
    db.add(inv); await db.flush()
    for item in items_data:
        qty = float(item.get("quantity", 1))
        price = float(item.get("unit_price", 0))
        db.add(InvoiceItem(
            invoice_id=inv.id,
            description=item.get("description",""),
            quantity=qty, unit_price=price, total=qty*price
        ))
    rec.invoices_generated = (rec.invoices_generated or 0) + 1
    rec.last_invoice_id = inv.id
    rec.next_run_date = _next_date(date.today().isoformat(), rec.frequency)
    if rec.end_date and rec.next_run_date > rec.end_date:
        rec.status = "ended"
    await db.commit(); await db.refresh(inv)
    return inv


@router.get("")
async def list_recurring(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RecurringInvoice).where(RecurringInvoice.user_id == user.id)
                               .order_by(RecurringInvoice.created_at.desc()))
    recs = result.scalars().all()
    client_ids = list({r.client_id for r in recs if r.client_id})
    clients = {}
    if client_ids:
        cr = await db.execute(select(Client).where(Client.id.in_(client_ids)))
        for c in cr.scalars().all(): clients[c.id] = c.name
    return [_rd(r, clients.get(r.client_id)) for r in recs]


@router.post("")
async def create_recurring(body: RecurringReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.frequency not in FREQ_DAYS:
        raise HTTPException(400, f"Frequency must be: {', '.join(FREQ_DAYS)}")
    items_data = [{"description": i.description, "quantity": i.quantity, "unit_price": i.unit_price} for i in body.items]
    rec = RecurringInvoice(
        user_id=user.id, client_id=body.client_id or None,
        title=body.title, items_json=json.dumps(items_data),
        tax_rate=body.tax_rate, discount=body.discount,
        currency=body.currency, notes=body.notes, terms=body.terms,
        frequency=body.frequency, start_date=body.start_date,
        end_date=body.end_date, next_run_date=body.start_date,
        auto_send=body.auto_send, status="active"
    )
    db.add(rec); await db.commit(); await db.refresh(rec)
    return _rd(rec)


@router.patch("/{rec_id}")
async def update_recurring(rec_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RecurringInvoice).where(RecurringInvoice.id == rec_id, RecurringInvoice.user_id == user.id))
    rec = result.scalar_one_or_none()
    if not rec: raise HTTPException(404, "Recurring invoice not found")
    allowed = ["status","auto_send","end_date","title","notes","terms"]
    for k, v in data.items():
        if k in allowed: setattr(rec, k, v)
    await db.commit()
    return {"success": True, "status": rec.status}


@router.delete("/{rec_id}")
async def delete_recurring(rec_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RecurringInvoice).where(RecurringInvoice.id == rec_id, RecurringInvoice.user_id == user.id))
    rec = result.scalar_one_or_none()
    if not rec: raise HTTPException(404, "Not found")
    await db.delete(rec); await db.commit()
    return {"success": True}


@router.post("/{rec_id}/generate-now")
async def generate_now(rec_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Manually trigger one invoice generation."""
    result = await db.execute(select(RecurringInvoice).where(RecurringInvoice.id == rec_id, RecurringInvoice.user_id == user.id))
    rec = result.scalar_one_or_none()
    if not rec: raise HTTPException(404, "Not found")
    inv = await _fire_invoice(rec, db)

    # Auto-send if enabled + client exists
    if rec.auto_send and rec.client_id:
        from app.services.email import send_invoice_email
        from app.models.invoice import InvoiceItem as IItem
        cl_res = await db.execute(select(Client).where(Client.id == rec.client_id))
        client = cl_res.scalar_one_or_none()
        items_res = await db.execute(select(IItem).where(IItem.invoice_id == inv.id))
        items = items_res.scalars().all()
        if client:
            import asyncio
            asyncio.create_task(send_invoice_email(
                to=client.email, client_name=client.name,
                sender_name=user.business_name or user.name,
                invoice_number=inv.invoice_number,
                amount=f"{inv.currency} {inv.total:,.2f}",
                due_date=inv.due_date, items=[],
                pay_url=f"{settings.FRONTEND_URL}/pay/{inv.public_token}",
                user_id=user.id, invoice_id=inv.id
            ))
            inv.status = "sent"; await db.commit()

    return {
        "success": True,
        "invoice_id": inv.id,
        "invoice_number": inv.invoice_number,
        "total": inv.total,
        "message": f"Invoice {inv.invoice_number} generated" + (" and sent" if rec.auto_send else " as draft")
    }


# ── Internal: run due recurring invoices (called by scheduler or cron) ────────

async def process_due_recurring():
    """Find all active recurring invoices due today and fire them."""
    from app.database import AsyncSessionLocal
    today = date.today().isoformat()
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(RecurringInvoice).where(
                RecurringInvoice.status == "active",
                RecurringInvoice.next_run_date <= today
            )
        )
        due = result.scalars().all()
        fired = 0
        for rec in due:
            try:
                inv = await _fire_invoice(rec, db)
                fired += 1
                if rec.auto_send and rec.client_id:
                    from app.services.email import send_invoice_email
                    from app.models.client import Client as C
                    from app.models.user import User as U
                    cl = await db.execute(select(C).where(C.id == rec.client_id))
                    client = cl.scalars().first()
                    ur = await db.execute(select(U).where(U.id == rec.user_id))
                    owner = ur.scalars().first()
                    if client and owner:
                        import asyncio
                        asyncio.create_task(send_invoice_email(
                            to=client.email, client_name=client.name,
                            sender_name=owner.business_name or owner.name,
                            invoice_number=inv.invoice_number,
                            amount=f"{inv.currency} {inv.total:,.2f}",
                            due_date=inv.due_date, items=[],
                            pay_url=f"{settings.FRONTEND_URL}/pay/{inv.public_token}",
                            user_id=owner.id, invoice_id=inv.id
                        ))
                        inv.status = "sent"; await db.commit()
            except Exception as e:
                import logging; logging.getLogger(__name__).error(f"Recurring fire error {rec.id}: {e}")
    return fired
