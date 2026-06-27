from sqlalchemy import String, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from .base import TimestampMixin, _uuid

class Proposal(Base, TimestampMixin):
    __tablename__ = "proposals"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    client_id: Mapped[str] = mapped_column(String(36), ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=True)   # Rich HTML/Markdown
    services: Mapped[list] = mapped_column(JSON, default=list)  # [{name, desc, price}]
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="NGN")
    status: Mapped[str] = mapped_column(String(30), default="draft")  # draft,sent,viewed,accepted,declined
    valid_days: Mapped[int] = mapped_column(default=30)
    public_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
    viewed_at: Mapped[str] = mapped_column(String(50), nullable=True)
    accepted_at: Mapped[str] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    terms: Mapped[str] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="proposals")
    client: Mapped["Client"] = relationship(back_populates="proposals")
    signature: Mapped["Signature"] = relationship(back_populates="proposal", uselist=False)
