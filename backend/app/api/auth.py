"""Auth endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.models.subscription import Subscription
from app.services.auth import hash_password, verify_password, create_token, get_current_user, generate_api_key
from app.services.email import send_welcome
import asyncio

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterReq(BaseModel):
    name: str
    email: EmailStr
    password: str
    business_name: str = ""
    country: str = "Nigeria"
    currency: str = "NGN"

class LoginReq(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(body: RegisterReq, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    user = User(
        name=body.name, email=body.email,
        password_hash=hash_password(body.password),
        business_name=body.business_name or body.name,
        country=body.country, currency=body.currency,
        api_key=generate_api_key()
    )
    db.add(user)
    await db.flush()
    sub = Subscription(user_id=user.id, plan="free", status="active")
    db.add(sub)
    await db.commit()
    await db.refresh(user)
    asyncio.create_task(send_welcome(user.email, user.name))
    token = create_token(user.id, user.email)
    return {"token": token, "user": {
        "id": user.id, "name": user.name, "email": user.email,
        "business_name": user.business_name, "plan": user.plan,
        "currency": user.currency, "country": user.country
    }}

@router.post("/login")
async def login(body: LoginReq, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(403, "Account deactivated")
    token = create_token(user.id, user.email)
    return {"token": token, "user": {
        "id": user.id, "name": user.name, "email": user.email,
        "business_name": user.business_name, "plan": user.plan,
        "currency": user.currency, "country": user.country,
        "phone": user.phone, "bank_name": user.bank_name,
        "bank_account": user.bank_account, "bank_account_name": user.bank_account_name
    }}

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "email": user.email,
            "business_name": user.business_name, "plan": user.plan,
            "currency": user.currency, "country": user.country,
            "phone": user.phone, "api_key": user.api_key,
            "bank_name": user.bank_name, "bank_account": user.bank_account,
            "bank_account_name": user.bank_account_name}

@router.put("/profile")
async def update_profile(data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    allowed = ["name","business_name","phone","country","currency","bank_name","bank_account","bank_account_name","business_logo"]
    for k, v in data.items():
        if k in allowed:
            setattr(user, k, v)
    await db.commit()
    return {"success": True, "message": "Profile updated"}
