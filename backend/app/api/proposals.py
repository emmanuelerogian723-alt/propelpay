"""Proposals — with AI draft + convert-to-invoice"""
import secrets
from datetime import datetime, date, timedelta
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
from app.models.invoice import Invoice, InvoiceItem
from app.services.auth import get_current_user
from app.services.ai import draft_proposal
from app.services.email import send_proposal_email
from app.config import get_settings
import asyncio, json

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
    signature_data: Optional[str] = None

def _pd(p: Proposal, client_name: str = None) -> dict:
    return {
        "id": p.id, "title": p.title, "content": p.content,
        "services": p.services, "total_amount": p.total_amount,
        "currency": p.currency, "status": p.status,
        "valid_days": p.valid_days, "public_token": p.public_token,
        "client_id": p.client_id, "client_name": client_name,
        "notes": p.notes, "terms": p.terms,
        "viewed_at": p.viewed_at, "accepted_at": p.accepted_at,
        "created_at": str(p.created_at)
    }

@router.get("")
async def list_proposals(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.user_id == user.id).order_by(Proposal.created_at.desc()))
    proposals = result.scalars().all()
    client_ids = list({p.client_id for p in proposals if p.client_id})
    clients = {}
    if client_ids:
        cr = await db.execute(select(Client).where(Client.id.in_(client_ids)))
        for c in cr.scalars().all(): clients[c.id] = c.name
    return [_pd(p, clients.get(p.client_id)) for p in proposals]

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
    db.add(p); await db.commit(); await db.refresh(p)
    return _pd(p)

@router.post("/ai-draft")
async def ai_draft(body: AIDraftReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    client_name = body.client_name or "Client"
    if body.client_id:
        res = await db.execute(select(Client).where(Client.id == body.client_id, Client.user_id == user.id))
        c = res.scalar_one_or_none()
        if c: client_name = c.name
    result = draft_proposal(
        business_name=user.business_name or user.name, client_name=client_name,
        service_type=body.service_type, scope=body.scope,
        budget=body.budget, tone=body.tone
    )
    return {
        "content": result["content"], "services": result["services"],
        "suggested_total": result["total"],
        "title": f"{body.service_type} Proposal for {client_name}"
    }

@router.get("/{proposal_id}")
async def get_proposal(proposal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    return _pd(p)

@router.put("/{proposal_id}")
async def update_proposal(proposal_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    for k, v in data.items():
        if k in ["title","content","services","total_amount","currency","valid_days","notes","terms","status"]:
            setattr(p, k, v)
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
    if not client: raise HTTPException(400, "Please attach a client before sending")
    p.status = "sent"; await db.commit()
    view_url = f"{settings.FRONTEND_URL}/p/{p.public_token}"
    asyncio.create_task(send_proposal_email(
        to=client.email, client_name=client.name,
        sender_name=user.business_name or user.name,
        proposal_title=p.title, view_url=view_url,
        user_id=user.id, proposal_id=p.id
    ))
    return {"success": True, "view_url": view_url, "message": f"Proposal sent to {client.email}"}

@router.post("/{proposal_id}/convert-to-invoice")
async def convert_to_invoice(proposal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """1-click: convert accepted proposal → draft invoice."""
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    if p.status not in ("accepted", "sent", "viewed"):
        raise HTTPException(400, "Only accepted or sent proposals can be converted")

    from sqlalchemy import func
    count_res = await db.execute(select(func.count(Invoice.id)).where(Invoice.user_id == user.id))
    count = count_res.scalar() or 0
    inv_number = f"INV-{date.today().strftime('%Y%m')}-{(count+1):04d}"
    token = secrets.token_urlsafe(32)
    services = p.services or []
    subtotal = sum(float(s.get("price", 0)) for s in services)
    due = (date.today() + timedelta(days=14)).strftime("%Y-%m-%d")

    inv = Invoice(
        user_id=user.id, client_id=p.client_id,
        invoice_number=inv_number,
        title=f"{p.title}",
        subtotal=subtotal, tax_rate=0, tax_amount=0,
        discount=0, total=subtotal,
        currency=p.currency, due_date=due,
        notes=p.notes, terms=p.terms,
        auto_reminders=True, public_token=token,
        status="draft"
    )
    db.add(inv); await db.flush()

    for svc in services:
        ii = InvoiceItem(
            invoice_id=inv.id,
            description=svc.get("name", svc.get("description", "Service")),
            quantity=1.0,
            unit_price=float(svc.get("price", 0)),
            total=float(svc.get("price", 0))
        )
        db.add(ii)

    # Link proposal → invoice
    p.status = "accepted"
    await db.commit(); await db.refresh(inv)

    return {
        "success": True,
        "invoice_id": inv.id,
        "invoice_number": inv.invoice_number,
        "total": inv.total,
        "currency": inv.currency,
        "message": f"Invoice {inv.invoice_number} created from proposal"
    }

@router.delete("/{proposal_id}")
async def delete_proposal(proposal_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.id == proposal_id, Proposal.user_id == user.id))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found")
    await db.delete(p); await db.commit()
    return {"success": True}

# ── Public view ───────────────────────────────────────────────────────────────

@router.get("/public/{token}")
async def public_proposal(token: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Proposal).where(Proposal.public_token == token))
    p = result.scalar_one_or_none()
    if not p: raise HTTPException(404, "Proposal not found or expired")
    if not p.viewed_at:
        p.viewed_at = datetime.utcnow().isoformat()
        if p.status == "sent": p.status = "viewed"
        await db.commit()
    res = await db.execute(select(User).where(User.id == p.user_id))
    sender = res.scalar_one_or_none()
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
    if p.status == "accepted": raise HTTPException(400, "Already signed")
    sig = Signature(proposal_id=p.id, signer_name=body.signer_name,
                    signer_email=body.signer_email, signature_data=body.signature_data,
                    ip_address=request.client.host, user_agent=request.headers.get("user-agent","")[:500])
    db.add(sig)
    p.status = "accepted"; p.accepted_at = datetime.utcnow().isoformat()
    await db.commit()
    return {"success": True, "message": "Proposal signed successfully!", "accepted_at": p.accepted_at}
