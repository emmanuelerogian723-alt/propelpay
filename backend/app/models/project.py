"""Project Tracker model"""
from sqlalchemy import Column, String, Float, Text, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid, enum
from app.models.base import Base

class ProjectStatus(str, enum.Enum):
    planning = "planning"
    active = "active"
    review = "review"
    completed = "completed"
    paused = "paused"

class Project(Base):
    __tablename__ = "projects"
    id           = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id      = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    client_id    = Column(String, ForeignKey("clients.id"), nullable=True)
    name         = Column(String(200), nullable=False)
    description  = Column(Text, nullable=True)
    status       = Column(String(30), default="active")
    budget       = Column(Float, default=0)
    currency     = Column(String(6), default="NGN")
    deadline     = Column(String(20), nullable=True)
    progress     = Column(Float, default=0)   # 0–100
    cover_image  = Column(Text, nullable=True)  # base64 or URL
    tags         = Column(Text, nullable=True)   # comma-separated
    invoice_id   = Column(String, nullable=True) # linked invoice
    notes        = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ProjectUpdate(Base):
    __tablename__ = "project_updates"
    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False, index=True)
    user_id    = Column(String, nullable=False)
    note       = Column(Text, nullable=False)
    image_url  = Column(Text, nullable=True)
    progress   = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
