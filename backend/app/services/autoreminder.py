"""
PropelPay Automatic Overdue Reminder + Late Fee Engine
-------------------------------------------------------
Runs on a background schedule (see main.py) so overdue invoices get chased
automatically even while the business owner is offline — no manual "send
reminder" click required. This is what makes the existing `auto_reminders`
flag on Invoice actually do something.

Escalation ladder (days overdue -> stage):
  1 day   -> stage 1  friendly nudge
  3 days  -> stage 2  firmer tone
  7 days  -> stage 3  urgent + late fee applied (if enabled)
  14 days -> stage 4  final-notice tone
  30 days -> stage 5  final notice, marked for manual follow-up

Each stage only fires once per invoice (tracked via `reminder_stage`), so a
single hourly sweep never double-sends. Late fees only ever apply once
(`late_fee_applied`), so re-running the sweep can't compound them.
"""
import logging
from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.invoice import Invoice
from app.models.client import Client
from app.models.user import User
from app.models.follow_up import FollowUp
from app.services.whatsapp import send_whatsapp_text, build_invoice_reminder
from app.services.payments import create_payment_link
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

# (days_overdue_threshold, stage_number)
ESCALATION_LADDER = [(1, 1), (3, 2), (7, 3), (14, 4), (30, 5)]
LATE_FEE_TRIGGER_STAGE = 3  # apply the late fee the same time stage-3 (day 7) fires


def _days_overdue(due_date_str: str) -> int:
    if not due_date_str:
        return 0
    try:
        due = datetime.strptime(due_date_str, "%Y-%m-%d").date()
    except ValueError:
        return 0
    return max(0, (date.today() - due).days)


def _target_stage(days_overdue: int) -> int:
    """Highest stage this invoice should have reached by now."""
    stage = 0
    for threshold, s in ESCALATION_LADDER:
        if days_overdue >= threshold:
            stage = s
    return stage


async def _ensure_payment_link(inv: Invoice, client: Client, user: User, db: AsyncSession) -> str:
    """Invoices sent through /invoices/{id}/send already have a Paystack link.
    This is a safety net for the rare invoice that reached 'sent' status without
    one (e.g. manually flipped, or Paystack was briefly down at send time)."""
    if inv.paystack_payment_link:
        return inv.paystack_payment_link
    if not settings.PAYSTACK_SECRET_KEY:
        return f"{settings.FRONTEND_URL}/pay/{inv.public_token}"
    try:
        cb = f"{settings.BACKEND_URL}/invoices/payment/verify/{inv.public_token}"
        result = await create_payment_link(
            email=client.email, amount=inv.total, currency=inv.currency,
            invoice_id=inv.id, invoice_number=inv.invoice_number,
            callback_url=cb, user_name=user.business_name or user.name
        )
        if result.get("authorization_url"):
            inv.paystack_payment_link = result["authorization_url"]
            return result["authorization_url"]
    except Exception as e:
        logger.error(f"autoreminder: payment link generation failed for invoice {inv.id}: {e}")
    return f"{settings.FRONTEND_URL}/pay/{inv.public_token}"


def _apply_late_fee(inv: Invoice) -> float:
    """Bumps invoice total by late_fee_percent, once. Returns the fee amount (0 if none)."""
    if not inv.late_fee_enabled or inv.late_fee_applied or inv.late_fee_percent <= 0:
        return 0.0
    fee = round(inv.total * (inv.late_fee_percent / 100), 2)
    inv.total = round(inv.total + fee, 2)
    inv.late_fee_applied = True
    note = f"\n[Auto] Late fee of {inv.currency} {fee:,.2f} ({inv.late_fee_percent}%) applied on {date.today().isoformat()} for non-payment."
    inv.notes = (inv.notes or "") + note
    return fee


async def process_overdue_invoices():
    """Main sweep — call this on a schedule. Safe to call repeatedly; it only
    acts on invoices that have crossed a new escalation threshold since the
    last run."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Invoice).where(
                Invoice.status.in_(["sent", "viewed", "partial", "overdue"]),
                Invoice.auto_reminders == True,  # noqa: E712
            )
        )
        invoices = result.scalars().all()
        sent, skipped, errors = 0, 0, 0

        for inv in invoices:
            try:
                days_overdue = _days_overdue(inv.due_date)
                if days_overdue <= 0:
                    continue  # not overdue yet, nothing to do

                target = _target_stage(days_overdue)
                if target <= (inv.reminder_stage or 0):
                    continue  # already handled this stage

                client_res = await db.execute(select(Client).where(Client.id == inv.client_id))
                client = client_res.scalar_one_or_none()
                if not client or not client.phone:
                    skipped += 1
                    continue

                user_res = await db.execute(select(User).where(User.id == inv.user_id))
                owner = user_res.scalar_one_or_none()
                if not owner:
                    skipped += 1
                    continue

                # Apply late fee first (so the reminder message shows the updated total)
                fee_applied = 0.0
                if target >= LATE_FEE_TRIGGER_STAGE:
                    fee_applied = _apply_late_fee(inv)

                pay_url = await _ensure_payment_link(inv, client, owner, db)

                # Deliberately NOT using the AI writer here: this job runs unattended
                # with nobody reviewing the message before it goes out to a real client.
                # The deterministic template already adjusts tone by days_overdue
                # (friendly -> warning -> urgent -> final notice) with zero AI-failure risk.
                # AI-personalized messages stay on the manual "remind" button, where the
                # owner can read the draft before it sends.
                message = build_invoice_reminder(
                    client_name=client.name,
                    sender_name=owner.business_name or owner.name,
                    invoice_number=inv.invoice_number,
                    amount=f"{inv.currency} {inv.total:,.2f}",
                    due_date=inv.due_date or "N/A",
                    pay_url=pay_url,
                    days_overdue=days_overdue,
                )
                if fee_applied:
                    message += f"\n\n_A late fee of {inv.currency} {fee_applied:,.2f} has been added to this invoice due to non-payment._"

                phone_id = owner.whatsapp_phone_id or settings.WHATSAPP_PHONE_ID
                wa_token = owner.whatsapp_access_token or settings.WHATSAPP_ACCESS_TOKEN
                wa_result = await send_whatsapp_text(
                    phone_number=client.phone, message=message,
                    phone_id=phone_id, access_token=wa_token,
                )

                db.add(FollowUp(
                    invoice_id=inv.id, type="whatsapp_auto", message=message,
                    sent=wa_result.get("success", False),
                    sent_at=datetime.utcnow().isoformat(),
                ))
                inv.reminder_stage = target
                inv.reminder_count = (inv.reminder_count or 0) + 1
                if days_overdue > 0 and inv.status not in ("overdue",):
                    inv.status = "overdue"

                await db.commit()
                sent += 1
                logger.info(
                    f"autoreminder: invoice {inv.invoice_number} -> stage {target} "
                    f"({days_overdue}d overdue), wa_success={wa_result.get('success')}, fee={fee_applied}"
                )
            except Exception as e:
                errors += 1
                logger.error(f"autoreminder: failed on invoice {inv.id}: {e}")
                await db.rollback()

        if sent or skipped or errors:
            logger.info(f"autoreminder sweep done: sent={sent} skipped={skipped} errors={errors}")
        return {"sent": sent, "skipped": skipped, "errors": errors}
