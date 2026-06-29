"""
Payments & Webhooks — Paystack inline + WhatsApp send
"""
import hmac, hashlib, json, asyncio, secrets, logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.client import Client
from app.models.payment import Payment
from app.models.follow_up import FollowUp
from app.services.auth import get_current_user
from app.services.payments import paystack_init, paystack_verify
from app.services.email import send_payment_received
from app.services.whatsapp import send_whatsapp_text, build_invoice_reminder
from app.services.ai import write_follow_up
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])


# ── Paystack Inline Init (public — called from invoice pay page) ──────────────

class PaystackInitReq(BaseModel):
    email: str
    invoice_token: str

@router.post("/pay/init")
async def init_paystack_payment(body: PaystackInitReq, db: AsyncSession = Depends(get_db)):
    """Initialize Paystack inline for a public invoice."""
    result = await db.execute(select(Invoice).where(Invoice.public_token == body.invoice_token))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status == "paid": raise HTTPException(400, "Invoice already paid")

    ref = f"pp_{inv.id[:8]}_{secrets.token_hex(8)}"
    amount_kobo = int(inv.total * 100)
    cb = f"{settings.BACKEND_URL}/webhooks/paystack/callback?token={inv.public_token}"

    result = await paystack_init(
        email=body.email or inv.public_token + "@pay.propelpay.io",
        amount_kobo=amount_kobo,
        reference=ref,
        callback_url=cb,
        metadata={
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "public_token": inv.public_token,
            "custom_fields": [
                {"display_name": "Invoice", "variable_name": "invoice_number", "value": inv.invoice_number},
                {"display_name": "Amount", "variable_name": "amount", "value": f"{inv.currency} {inv.total:,.2f}"}
            ]
        }
    )
    if result.get("authorization_url"):
        # Store link on invoice
        inv.paystack_payment_link = result["authorization_url"]
        await db.commit()
        return {
            "authorization_url": result["authorization_url"],
            "access_code": result.get("access_code"),
            "reference": ref,
            "public_key": settings.PAYSTACK_PUBLIC_KEY,
            "amount": amount_kobo,
            "currency": "NGN",
            "email": body.email
        }
    raise HTTPException(500, result.get("error", "Paystack init failed"))


# ── Paystack Webhook (server-to-server from Paystack) ────────────────────────

@router.post("/webhooks/paystack")
async def paystack_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handles Paystack charge.success webhook — marks invoice paid."""
    body = await request.body()
    sig = request.headers.get("x-paystack-signature", "")

    if settings.PAYSTACK_SECRET_KEY and sig:
        expected = hmac.new(settings.PAYSTACK_SECRET_KEY.encode(), body, hashlib.sha512).hexdigest()
        if sig != expected:
            raise HTTPException(400, "Invalid signature")

    try:
        data = json.loads(body)
        event = data.get("event", "")
        charge = data.get("data", {})
        if event != "charge.success" and charge.get("status") != "success":
            return {"status": "ignored"}

        meta = charge.get("metadata", {})
        invoice_id = meta.get("invoice_id") or charge.get("metadata", {}).get("invoice_id")
        ref = charge.get("reference", "")

        inv = None
        if invoice_id:
            res = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
            inv = res.scalar_one_or_none()
        if not inv:
            # Try by reference stored on payment link URL
            pub_token = meta.get("public_token")
            if pub_token:
                res = await db.execute(select(Invoice).where(Invoice.public_token == pub_token))
                inv = res.scalar_one_or_none()

        if inv and inv.status != "paid":
            inv.status = "paid"
            inv.paid_at = datetime.utcnow().isoformat()
            pay = Payment(invoice_id=inv.id, user_id=inv.user_id,
                          amount=inv.total, currency=inv.currency,
                          provider="paystack", reference=ref, status="paid")
            db.add(pay)
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
        logger.error(f"Webhook error: {e}")
    return {"status": "ok"}


@router.get("/webhooks/paystack/callback")
async def paystack_callback(token: str, reference: str = None, trxref: str = None, db: AsyncSession = Depends(get_db)):
    """Browser redirect after Paystack payment."""
    ref = reference or trxref
    if ref:
        verify = await paystack_verify(ref)
        if verify.get("success"):
            result = await db.execute(select(Invoice).where(Invoice.public_token == token))
            inv = result.scalar_one_or_none()
            if inv and inv.status != "paid":
                inv.status = "paid"; inv.paid_at = datetime.utcnow().isoformat()
                await db.commit()
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/pay/{token}?paid=1")
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/pay/{token}?status=pending")


# ── WhatsApp Reminder ─────────────────────────────────────────────────────────

class WAReq(BaseModel):
    invoice_id: str
    custom_message: Optional[str] = None

@router.post("/invoices/{invoice_id}/send-whatsapp")
async def send_whatsapp_reminder(
    invoice_id: str,
    body: WAReq = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = result.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    if inv.status == "paid": raise HTTPException(400, "Invoice already paid")

    client = None
    if inv.client_id:
        cr = await db.execute(select(Client).where(Client.id == inv.client_id))
        client = cr.scalar_one_or_none()
    if not client or not client.phone:
        raise HTTPException(400, "Client has no phone number. Add one in the Clients tab first.")

    from datetime import date
    days_overdue = 0
    if inv.due_date:
        due = datetime.strptime(inv.due_date, "%Y-%m-%d").date()
        days_overdue = max(0, (date.today() - due).days)

    pay_url = inv.paystack_payment_link or f"{settings.FRONTEND_URL}/pay/{inv.public_token}"

    # AI message if no custom message
    custom = body.custom_message if body else None
    if not custom:
        custom = write_follow_up(
            client_name=client.name,
            invoice_number=inv.invoice_number,
            amount=inv.total, currency=inv.currency,
            days_overdue=days_overdue,
            business_name=user.business_name or user.name,
            attempt=(inv.reminder_count or 0) + 1
        )

    message = build_invoice_reminder(
        client_name=client.name,
        sender_name=user.business_name or user.name,
        invoice_number=inv.invoice_number,
        amount=f"{inv.currency} {inv.total:,.2f}",
        due_date=inv.due_date or "N/A",
        pay_url=pay_url,
        days_overdue=days_overdue,
        custom_message=custom
    )

    # Use per-user WA config if set, else global env
    phone_id = user.whatsapp_phone_id or settings.WHATSAPP_PHONE_ID
    wa_token = user.whatsapp_access_token or settings.WHATSAPP_ACCESS_TOKEN

    wa_result = await send_whatsapp_text(
        phone_number=client.phone,
        message=message,
        phone_id=phone_id,
        access_token=wa_token
    )

    # Log in follow_ups
    fu = FollowUp(invoice_id=inv.id, type="whatsapp", message=message,
                  sent=wa_result.get("success", False),
                  sent_at=datetime.utcnow().isoformat())
    inv.reminder_count = (inv.reminder_count or 0) + 1
    db.add(fu); await db.commit()

    if wa_result.get("success"):
        return {"success": True, "message": f"WhatsApp sent to {client.phone}", "message_id": wa_result.get("message_id"), "preview": message}
    else:
        return {"success": False, "error": wa_result.get("error"), "preview": message,
                "message": "WhatsApp not configured — add WHATSAPP_PHONE_ID and WHATSAPP_ACCESS_TOKEN to Render env vars"}


# ── WhatsApp Webhook (Meta sends delivery status here) ───────────────────────

@router.get("/webhooks/whatsapp")
async def wa_webhook_verify(hub_mode: str = None, hub_challenge: str = None,
                              hub_verify_token: str = None):
    """Meta webhook verification handshake."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    raise HTTPException(403, "Forbidden")

@router.post("/webhooks/whatsapp")
async def wa_webhook_receive(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive WhatsApp delivery status updates."""
    try:
        data = await request.json()
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                statuses = change.get("value", {}).get("statuses", [])
                for s in statuses:
                    wam_id = s.get("id"); status = s.get("status")
                    logger.info(f"WhatsApp delivery: {wam_id} → {status}")
                    # Update follow_up record if we stored the message_id
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
    return {"status": "ok"}
