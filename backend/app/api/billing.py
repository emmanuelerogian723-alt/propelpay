"""Subscription & Billing endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.services.auth import get_current_user
from app.services.payments import paystack_init, paystack_verify
from app.config import get_settings
import secrets

settings = get_settings()
router = APIRouter(prefix="/billing", tags=["billing"])

PLANS = {
    "free":       {"name": "Free",       "price_ngn": 0,     "price_usd": 0},
    "solo":       {"name": "Solo",       "price_ngn": 9900,  "price_usd": 15},
    "agency":     {"name": "Agency",     "price_ngn": 24900, "price_usd": 29},
    "enterprise": {"name": "Enterprise", "price_ngn": 79900, "price_usd": 79},
}

@router.get("/plans")
async def get_plans():
    return {"plans": PLANS, "limits": settings.PLAN_LIMITS}

@router.get("/subscription")
async def get_subscription(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
    sub = res.scalar_one_or_none()
    return {"plan": user.plan, "subscription": {
        "plan": sub.plan if sub else "free", "status": sub.status if sub else "active",
        "current_period_end": sub.current_period_end if sub else None
    }, "limits": settings.PLAN_LIMITS.get(user.plan, settings.PLAN_LIMITS["free"])}

@router.post("/upgrade")
async def initiate_upgrade(body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    plan = body.get("plan", "solo")
    if plan not in PLANS or plan == "free":
        raise HTTPException(400, "Invalid plan")
    
    price = PLANS[plan]["price_ngn"]
    reference = f"pp_sub_{user.id[:8]}_{secrets.token_hex(8)}"
    cb = f"{settings.BACKEND_URL}/billing/verify/{reference}"
    
    result = await paystack_init(
        email=user.email, amount_kobo=price * 100,
        reference=reference, callback_url=cb,
        metadata={"user_id": user.id, "plan": plan, "type": "subscription"}
    )
    if result.get("authorization_url"):
        return {"authorization_url": result["authorization_url"], "reference": reference, "plan": plan}
    raise HTTPException(500, result.get("error", "Payment initialization failed"))

@router.get("/verify/{reference}")
async def verify_upgrade(reference: str, db: AsyncSession = Depends(get_db)):
    verify = await paystack_verify(reference)
    if verify.get("success"):
        data = verify["data"]
        meta = data.get("metadata", {})
        user_id = meta.get("user_id")
        plan = meta.get("plan", "solo")
        if user_id:
            res = await db.execute(select(User).where(User.id == user_id))
            user = res.scalar_one_or_none()
            if user:
                user.plan = plan
                sub_res = await db.execute(select(Subscription).where(Subscription.user_id == user.id))
                sub = sub_res.scalar_one_or_none()
                if sub:
                    sub.plan = plan; sub.status = "active"; sub.reference = reference
                await db.commit()
        return {"success": True, "plan": plan, "message": f"Upgraded to {plan.title()} plan!"}
    return {"success": False, "message": "Payment verification failed"}
