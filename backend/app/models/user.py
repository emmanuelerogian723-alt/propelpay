from sqlalchemy import String, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import TimestampMixin, _uuid

class User(Base, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    business_name: Mapped[str] = mapped_column(String(255), nullable=True)
    business_logo: Mapped[str] = mapped_column(Text, nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=True, default="Nigeria")
    currency: Mapped[str] = mapped_column(String(10), nullable=True, default="NGN")
    plan: Mapped[str] = mapped_column(String(30), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    api_key: Mapped[str] = mapped_column(String(80), unique=True, nullable=True, index=True)
    # Legacy single bank (kept for compatibility)
    bank_name: Mapped[str] = mapped_column(String(100), nullable=True)
    bank_account: Mapped[str] = mapped_column(String(50), nullable=True)
    bank_account_name: Mapped[str] = mapped_column(String(255), nullable=True)
    paystack_subaccount: Mapped[str] = mapped_column(String(100), nullable=True)
    # AI insights cache
    ai_insights_cache: Mapped[str] = mapped_column(Text, nullable=True)
    ai_insights_cached_at: Mapped[str] = mapped_column(String(30), nullable=True)

    clients: Mapped[list["Client"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    proposals: Mapped[list["Proposal"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bank_accounts: Mapped[list["BankAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
