"""PropelPay Auth Service"""
import secrets, string
from datetime import datetime, timedelta
from typing import Optional
import bcrypt, jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.database import get_db
from app.models.user import User

settings = get_settings()
bearer = HTTPBearer(auto_error=False)

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())

def create_token(user_id: str, email: str) -> str:
    exp = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    return jwt.encode({"sub": user_id, "email": email, "exp": exp},
                      settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

def generate_api_key() -> str:
    alpha = string.ascii_letters + string.digits
    return "pp_" + "".join(secrets.choice(alpha) for _ in range(48))

def generate_token(n: int = 32) -> str:
    return secrets.token_urlsafe(n)

async def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Security(bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not creds:
        raise HTTPException(401, "Missing Authorization header")
    payload = decode_token(creds.credentials)
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return user

async def get_user_optional(
    creds: Optional[HTTPAuthorizationCredentials] = Security(bearer),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not creds:
        return None
    try:
        return await get_current_user(creds, db)
    except:
        return None
