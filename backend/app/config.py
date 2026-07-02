"""PropelPay Configuration — Pydantic v2"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8",
        extra="ignore", case_sensitive=False,
    )
    APP_NAME: str = "PropelPay"
    VERSION: str = "3.0.0"
    ENVIRONMENT: str = "development"
    SECRET_KEY: str = "change-me-propelpay-secret-2026"
    FRONTEND_URL: str = "http://localhost:8000"
    BACKEND_URL: str = "http://localhost:8000"
    DATABASE_URL: str = "sqlite+aiosqlite:///./propelpay.db"
    JWT_SECRET_KEY: str = "propelpay-jwt-secret-2026-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 720

    # AI
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Payments — Paystack
    PAYSTACK_SECRET_KEY: str = ""
    PAYSTACK_PUBLIC_KEY: str = ""

    # Email — Resend (primary, free 3k/month)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = ""

    # Email — SMTP fallback
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "PropelPay"
    SMTP_FROM_EMAIL: str = ""

    # Admin — protects manual trigger endpoints (e.g. force an overdue sweep)
    ADMIN_SECRET: str = ""

    # WhatsApp Business API (Meta Cloud API)
    WHATSAPP_PHONE_ID: str = ""          # Phone Number ID from Meta dashboard
    WHATSAPP_ACCESS_TOKEN: str = ""      # Permanent system user token
    WHATSAPP_API_VERSION: str = "v19.0"
    WHATSAPP_VERIFY_TOKEN: str = "propelpay_wa_verify_2026"

    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT != "production"

    @property
    def PLAN_LIMITS(self) -> dict:
        return {
            "free":       {"proposals": 3,  "invoices": 5,  "clients": 5,  "ai_drafts": 3,  "recurring": 0},
            "solo":       {"proposals": 50, "invoices": 100,"clients": 50, "ai_drafts": 50, "recurring": 5},
            "agency":     {"proposals": -1, "invoices": -1, "clients": -1, "ai_drafts": -1, "recurring": -1},
            "enterprise": {"proposals": -1, "invoices": -1, "clients": -1, "ai_drafts": -1, "recurring": -1},
        }

    @property
    def PLAN_PRICES_NGN(self) -> dict:
        return {"free": 0, "solo": 9900, "agency": 24900, "enterprise": 79900}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
