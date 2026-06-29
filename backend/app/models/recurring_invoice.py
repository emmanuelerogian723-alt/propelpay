"""Recurring / retainer invoice model"""
from sqlalchemy import String, Float, Boolean, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import TimestampMixin, _uuid

class RecurringInvoice(Base, TimestampMixin):
    __tablename__ = "recurring_invoices"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    # Template fields (copied to each generated invoice)
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    items_json: Mapped[str] = mapped_column(Text, nullable=True)   # JSON list of line items
    tax_rate: Mapped[float] = mapped_column(Float, default=0.0)
    discount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="NGN")
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    terms: Mapped[str] = mapped_column(Text, nullable=True)
    # Schedule
    frequency: Mapped[str] = mapped_column(String(20), default="monthly")  # weekly/monthly/quarterly/yearly
    start_date: Mapped[str] = mapped_column(String(20), nullable=False)
    end_date: Mapped[str] = mapped_column(String(20), nullable=True)
    next_run_date: Mapped[str] = mapped_column(String(20), nullable=True)
    auto_send: Mapped[bool] = mapped_column(Boolean, default=True)
    # State
    status: Mapped[str] = mapped_column(String(20), default="active")  # active/paused/ended
    invoices_generated: Mapped[int] = mapped_column(Integer, default=0)
    last_invoice_id: Mapped[str] = mapped_column(String(36), nullable=True)

    user: Mapped["User"] = relationship(back_populates="recurring_invoices")
