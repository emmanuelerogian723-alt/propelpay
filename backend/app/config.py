"""PropelPay Configuration"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PropelPay"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = ENVIRONMENT != "production"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-super-secret-key-propelpay-2026")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./propelpay.db")

    # Auth
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "propelpay-jwt-secret-2026-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 720  # 30 days

    # AI
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Payments
    PAYSTACK_SECRET_KEY: str = os.getenv("PAYSTACK_SECRET_KEY", "")
    PAYSTACK_PUBLIC_KEY: str = os.getenv("PAYSTACK_PUBLIC_KEY", "")
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")  # future

    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "PropelPay")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", os.getenv("SMTP_USER", ""))

    # Plans & Limits
    PLAN_LIMITS: dict = {
        "free":       {"proposals": 3,  "invoices": 5,  "clients": 5,   "ai_drafts": 3},
        "solo":       {"proposals": 50, "invoices": 100,"clients": 50,  "ai_drafts": 50},
        "agency":     {"proposals": -1, "invoices": -1, "clients": -1,  "ai_drafts": -1},
        "enterprise": {"proposals": -1, "invoices": -1, "clients": -1,  "ai_drafts": -1},
    }
    # Prices in Naira (kobo for Paystack)
    PLAN_PRICES_NGN: dict = {
        "free":       0,
        "solo":       9900,    # ₦9,900/mo
        "agency":     24900,   # ₦24,900/mo
        "enterprise": 79900,   # ₦79,900/mo
    }
    # Prices in USD cents for Stripe
    PLAN_PRICES_USD: dict = {
        "free":       0,
        "solo":       1500,    # $15/mo
        "agency":     2900,    # $29/mo
        "enterprise": 7900,    # $79/mo
    }

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
