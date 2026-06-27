"""PropelPay Payment Service — Paystack primary, Stripe ready"""
import logging, httpx
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
PAYSTACK_BASE = "https://api.paystack.co"


async def paystack_init(email: str, amount_kobo: int, reference: str,
                         callback_url: str, metadata: dict = None) -> dict:
    """Initialize a Paystack payment."""
    if not settings.PAYSTACK_SECRET_KEY:
        return {"error": "Paystack not configured", "authorization_url": None}
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
               "Content-Type": "application/json"}
    payload = {
        "email": email, "amount": amount_kobo,
        "reference": reference, "callback_url": callback_url,
        "metadata": metadata or {}
    }
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(f"{PAYSTACK_BASE}/transaction/initialize",
                                 json=payload, headers=headers)
        data = resp.json()
        if data.get("status"):
            return {"authorization_url": data["data"]["authorization_url"],
                    "access_code": data["data"]["access_code"],
                    "reference": data["data"]["reference"]}
        return {"error": data.get("message", "Paystack error")}


async def paystack_verify(reference: str) -> dict:
    """Verify a Paystack transaction."""
    if not settings.PAYSTACK_SECRET_KEY:
        return {"error": "Paystack not configured"}
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{PAYSTACK_BASE}/transaction/verify/{reference}",
                                headers=headers)
        data = resp.json()
        if data.get("status") and data["data"]["status"] == "success":
            return {"success": True, "data": data["data"],
                    "amount": data["data"]["amount"] / 100}  # kobo to naira
        return {"success": False, "status": data.get("data", {}).get("status", "failed")}


async def create_payment_link(email: str, amount: float, currency: str,
                               invoice_id: str, invoice_number: str,
                               callback_url: str, user_name: str) -> dict:
    """Create a payment link for an invoice."""
    import secrets
    reference = f"pp_inv_{invoice_id[:8]}_{secrets.token_hex(8)}"
    amount_kobo = int(amount * 100) if currency == "NGN" else int(amount * 100)
    return await paystack_init(
        email=email, amount_kobo=amount_kobo, reference=reference,
        callback_url=callback_url,
        metadata={"invoice_id": invoice_id, "invoice_number": invoice_number, "billed_by": user_name}
    )
