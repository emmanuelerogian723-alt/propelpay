"""Chatbot Lead model — captures name/email/WhatsApp from the AI widget"""
from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
import uuid
from app.models.base import Base


class ChatLead(Base):
    __tablename__ = "chat_leads"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name       = Column(String(200), nullable=False)
    email      = Column(String(200), nullable=False)
    whatsapp   = Column(String(50), nullable=False)
    note       = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
