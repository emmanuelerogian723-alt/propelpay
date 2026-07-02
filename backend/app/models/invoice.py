from sqlalchemy import String, Text, Float, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import TimestampMixin, _uuid

class InvoiceItem(Base, TimestampMixin):
    __tablename__ = "invoice_items"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"))
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, default=1.0)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total: Mapped[float] = mapped_column(Float, nullable=False)
    invoice: Mapped["Invoice"] = relationship(back_populates="items")

class Invoice(Base, TimestampMixin):
    __tablename__ = "invoices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    subtotal: Mapped[float] = mapped_column(Float, default=0.0)
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, default=0.0)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    total: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="NGN")
    status: Mapped[str] = mapped_column(String(30), default="draft")  # draft,sent,viewed,partial,paid,overdue,cancelled
    due_date: Mapped[str] = mapped_column(String(20), nullable=True)
    paid_at: Mapped[str] = mapped_column(String(50), nullable=True)
    public_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    paystack_payment_link: Mapped[str] = mapped_column(Text, nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    terms: Mapped[str] = mapped_column(Text, nullable=True)
    auto_reminders: Mapped[bool] = mapped_column(Boolean, default=True)
    reminder_count: Mapped[int] = mapped_column(Integer, default=0)
    reminder_stage: Mapped[int] = mapped_column(Integer, default=0)  # 0=none,1=day1,2=day3,3=day7,4=day14,5=day30
    late_fee_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    late_fee_percent: Mapped[float] = mapped_column(Float, default=0.0)
    late_fee_applied: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship(back_populates="invoices")
    client: Mapped["Client"] = relationship(back_populates="invoices")
    items: Mapped[list["InvoiceItem"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
    follow_ups: Mapped[list["FollowUp"]] = relationship(back_populates="invoice", cascade="all, delete-orphan")
