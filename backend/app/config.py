"""PropelPay Configuration — Pydantic v2"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        extra="ignore", case_sensitive=False,
    )
    APP_NAME: str = "PropelPay"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-super-secret-key-propelpay-2026"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "sqlite+aiosqlite:///./propelpay.db"
    JWT_SECRET_KEY: str = "propelpay-jwt-secret-2026-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 720

    # AI
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Payments
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""

    # Email — Resend (primary, free 3k/month, https://resend.com)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""           # e.g. noreply@yourdomain.com

    # Email — SMTP fallback
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "PropelPay"
    SMTP_FROM_EMAIL: str = ""

    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT != "production"

    @property
    def PLAN_LIMITS(self) -> dict:
        return {
            "free":       {"proposals": 3,  "invoices": 5,  "clients": 5,  "ai_drafts": 3},
            "solo":       {"proposals": 50, "invoices": 100,"clients": 50, "ai_drafts": 50},
            "agency":     {"proposals": -1, "invoices": -1, "clients": -1, "ai_drafts": -1},
            "enterprise": {"proposals": -1, "invoices": -1, "clients": -1, "ai_drafts": -1},
        }
    @property
    def PLAN_PRICES_NGN(self) -> dict:
        return {"free": 0, "solo": 9900, "agency": 24900, "enterprise": 79900}
    @property
    def PLAN_PRICES_USD(self) -> dict:
        return {"free": 0, "solo": 1500, "agency": 2900, "enterprise": 7900}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
