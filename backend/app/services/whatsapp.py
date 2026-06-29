"""PropelPay WhatsApp Business API Service (Meta Cloud API)"""
import logging
import httpx
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
WA_BASE = "https://graph.facebook.com"


async def send_whatsapp_text(
    phone_number: str,
    message: str,
    phone_id: str = None,
    access_token: str = None
) -> dict:
    """Send a plain text WhatsApp message."""
    pid   = phone_id    or settings.WHATSAPP_PHONE_ID
    token = access_token or settings.WHATSAPP_ACCESS_TOKEN
    ver   = settings.WHATSAPP_API_VERSION or "v19.0"

    if not pid or not token:
        logger.warning("WhatsApp not configured — WHATSAPP_PHONE_ID or WHATSAPP_ACCESS_TOKEN missing")
        return {"success": False, "error": "WhatsApp not configured"}

    # Normalize phone: remove spaces, dashes; ensure E.164 format
    clean = "".join(c for c in phone_number if c.isdigit() or c == "+")
    if not clean.startswith("+"): clean = "+234" + clean.lstrip("0")  # Default Nigeria

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type":    "individual",
        "to":                clean,
        "type":              "text",
        "text":              {"preview_url": True, "body": message}
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{WA_BASE}/{ver}/{pid}/messages",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=payload
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("messages"):
                wam_id = data["messages"][0].get("id")
                logger.info(f"WhatsApp sent to {clean}: {wam_id}")
                return {"success": True, "message_id": wam_id, "to": clean}
            err = data.get("error", {}).get("message", str(data))
            logger.error(f"WhatsApp API error: {err}")
            return {"success": False, "error": err}
    except Exception as e:
        logger.error(f"WhatsApp exception: {e}")
        return {"success": False, "error": str(e)}


def build_invoice_reminder(
    client_name: str,
    sender_name: str,
    invoice_number: str,
    amount: str,
    due_date: str,
    pay_url: str,
    days_overdue: int = 0,
    custom_message: str = ""
) -> str:
    """Build a professional WhatsApp invoice reminder message."""
    if custom_message:
        return custom_message

    urgency = ""
    if days_overdue > 30:
        urgency = "🔴 *FINAL NOTICE*\n\n"
    elif days_overdue > 7:
        urgency = "⚠️ *URGENT* — "
    elif days_overdue > 0:
        urgency = "⚠️ "

    overdue_line = f"This invoice is *{days_overdue} days overdue*." if days_overdue > 0 else f"This invoice is due on *{due_date}*."

    return f"""{urgency}Hello {client_name} 👋

This is a friendly reminder from *{sender_name}*.

📄 *Invoice:* {invoice_number}
💰 *Amount Due:* {amount}
📅 *Due Date:* {due_date}

{overdue_line}

To pay securely, click the link below:
👉 {pay_url}

Thank you for your business. Please reach out if you have any questions.

— {sender_name} via PropelPay ⚡"""
