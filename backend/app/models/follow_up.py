from sqlalchemy import String, Text, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import TimestampMixin, _uuid

class FollowUp(Base, TimestampMixin):
    __tablename__ = "follow_ups"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    invoice_id: Mapped[str] = mapped_column(String(36), ForeignKey("invoices.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(30), default="email")  # email, whatsapp, sms
    message: Mapped[str] = mapped_column(Text, nullable=True)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_at: Mapped[str] = mapped_column(String(50), nullable=True)
    invoice: Mapped["Invoice"] = relationship(back_populates="follow_ups")
