"""Proposals endpoints"""
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.proposal import Proposal
from app.models.signature import Signature
from app.models.client import Client
from app.services.auth import get_current_user
from app.services.ai import draft_proposal
from app.services.email import send_proposal_notification
from app.config import get_settings
import asyncio

settings = get_settings()
router = APIRouter(prefix="/proposals", tags=["proposals"])

class ServiceItem(BaseModel):
    name: str
    description: str = ""
    price: float = 0

class ProposalReq(BaseModel):
    title: str
    client_id: Optional[str] = None
    content: Optional[str] = None
    services: List[ServiceItem] = []
    total_amount: float = 0
    currency: str = "NGN"
    valid_days: int = 30
    notes: Optional[str] = None
    terms: Optional[str] = None

class AIDraftReq(BaseModel):
    client_id: Optional[str] = None
    client_name: Optional[str] = None
    service_type: str
    scope: str
    budget: Optional[str] = None
    tone: str = "professional"

class SignReq(BaseModel):
    signer_name: str
    signer_email: str
    signature_data: Optional[str] = None  # base64 SVG

def _proposal_dict(p: Proposal) -> dict:
    return {
        "id": p.id, "title": p.title, "content": p.content,
        "services": p.services, "total_amount": p.total_amount,
        "currency": p.currency, "status": p.status,
        "valid_days": p.valid_days, "public_token": p.public_token,
        "client_id": p.client_id, "notes": p.notes, "terms": p.terms,
        "viewed_at": p.viewed_at, "accepted_at": p.accepted_at,
        "created_at": str(p.created_at)
    }

@router.get("")
async def list_proposals(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.user_id == user.id).order_by(Proposal.created_at.desc()))
    return [_proposal_dict(p) for p in result.scalars().all()]

@router.post("")
async def create_proposal(body: ProposalReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    token = secrets.token_urlsafe(32)
    total = sum(s.price for s in body.services) if body.services else body.total_amount
    p = Proposal(
        user_id=user.id, title=body.title, client_id=body.client_id,
        content=body.content, services=[s.model_dump() for s in body.services],
        total_amount=total, currency=body.currency, valid_days=body.valid_days,
        notes=body.notes, terms=body.terms, public_token=token, status="draft"
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return _proposal_dict(p)

@router.post("/ai-draft")
async def ai_draft(body: AIDraftReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Generate a full proposal using AI."""
    client_name = body.client_name or "Client"
    if body.client_id:
        res = await db.execute(select(Client).where(Client.id == body.client_id, Client.user_id == user.id))
        c = res.scalar_one_or_none()
        if c: client_name = c.name

    result = draft_proposal(
        business_name=user.business_name or user.name,
        client_name=client_name,
        service_type=body.service_type,
        scope=body.scope,
        budget=body.budget,
        tone=body.tone
    )
    return {
        "content": result["content"],
        "services": result["services"],
        "suggested_total": result["total"],
        "title": f"{body.service_type} Proposal for {client_name}"
    }

@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    return _proposal_dict(p)

@router.put("/{proposal_id}")
async def update_proposal(proposal_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    allowed = ["title","content","services","total_amount","currency","valid_days","notes","terms","status"]
    for k, v in data.items():
        if k in allowed: setattr(p, k, v)
    if "services" in data:
        p.total_amount = sum(s.get("price", 0) for s in data["services"])
    await db.commit()
    return {"success": True}

@router.post("/{proposal_id}/send")
async def send_proposal(proposal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    
    client = None
    if p.client_id:
        res = await db.execute(select(Client).where(Client.id == p.client_id))
        client = res.scalar_one_or_none()
    
    p.status = "sent"
    await db.commit()
    
    view_url = f"{settings.FRONTEND_URL}/p/{p.public_token}"
    if client:
        asyncio.create_task(send_proposal_notification(
            client.email, client.name, user.business_name or user.name,
            p.title, view_url
        ))
    return {"success": True, "view_url": view_url, "message": f"Proposal sent to {client.email if client else 'client'}"}

@router.delete("/{proposal_id}")
async def delete_proposal(proposal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    await db.delete(p)
    await db.commit()
    return {"success": True}

# ── Public proposal view (no auth) ──────────────────────────────────────────

@router.get("/public/{token}")
async def public_proposal(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.public_token == token))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found or expired")
    
    # Track first view
    if not p.viewed_at:
        p.viewed_at = datetime.utcnow().isoformat()
        if p.status == "sent": p.status = "viewed"
        await db.commit()
    
    # Get sender info
    res = await db.execute(select(User).where(User.id == p.user_id))
    sender = res.scalar_one_or_none()
    
    # Check signature
    sig_res = await db.execute(select(Signature).where(Signature.proposal_id == p.id))
    sig = sig_res.scalar_one_or_none()
    
    return {
        "id": p.id, "title": p.title, "content": p.content,
        "services": p.services, "total_amount": p.total_amount,
        "currency": p.currency, "status": p.status,
        "valid_days": p.valid_days, "notes": p.notes, "terms": p.terms,
        "accepted_at": p.accepted_at, "created_at": str(p.created_at),
        "sender": {
            "name": sender.name if sender else "Business",
            "business_name": sender.business_name if sender else "",
            "email": sender.email if sender else "",
        },
        "signed": sig is not None,
        "signature": {"signer_name": sig.signer_name, "signed_at": str(sig.created_at)} if sig else None
    }

@router.post("/public/{token}/sign")
async def sign_proposal(token: str, body: SignReq, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.public_token == token))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    if p.status in ("accepted",): raise HTTPException(400, "Already signed")
    
    sig = Signature(
        proposal_id=p.id,
        signer_name=body.signer_name,
        signer_email=body.signer_email,
        signature_data=body.signature_data,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "")[:500]
    )
    db.add(sig)
    p.status = "accepted"
    p.accepted_at = datetime.utcnow().isoformat()
    await db.commit()
    return {"success": True, "message": "Proposal signed successfully!", "accepted_at": p.accepted_at}
