"""Email delivery tracking model"""
from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base
from .base import TimestampMixin, _uuid

class EmailLog(Base, TimestampMixin):
    __tablename__ = "email_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=True)
    proposal_id: Mapped[str] = mapped_column(String(36), nullable=True)
    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    email_type: Mapped[str] = mapped_column(String(50), nullable=False)  # invoice, proposal, reminder, welcome, receipt
    status: Mapped[str] = mapped_column(String(30), default="queued")    # queued, sent, delivered, failed, opened
    provider: Mapped[str] = mapped_column(String(30), default="resend")  # resend, smtp, skipped
    resend_id: Mapped[str] = mapped_column(String(100), nullable=True)   # provider message ID
    error_msg: Mapped[str] = mapped_column(Text, nullable=True)
    retries: Mapped[int] = mapped_column(default=0)
