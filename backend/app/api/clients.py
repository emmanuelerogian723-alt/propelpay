"""Client management endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.client import Client
from app.services.auth import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])

class ClientReq(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

@router.get("")
async def list_clients(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.user_id == user.id).order_by(Client.created_at.desc()))
    clients = result.scalars().all()
    return [{"id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
             "company": c.company, "address": c.address, "created_at": str(c.created_at)} for c in clients]

@router.post("")
async def create_client(body: ClientReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    client = Client(user_id=user.id, **body.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return {"id": client.id, "name": client.name, "email": client.email, "message": "Client added"}

@router.get("/{client_id}")
async def get_client(client_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == user.id))
    c = result.scalar_one_or_none()
    if not c: raise HTTPException(404, "Client not found")
    return {"id": c.id, "name": c.name, "email": c.email, "phone": c.phone,
            "company": c.company, "address": c.address, "notes": c.notes}

@router.put("/{client_id}")
async def update_client(client_id: str, data: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == user.id))
    c = result.scalar_one_or_none()
    if not c: raise HTTPException(404, "Client not found")
    for k, v in data.items():
        if hasattr(c, k) and k not in ("id","user_id"):
            setattr(c, k, v)
    await db.commit()
    return {"success": True}

@router.delete("/{client_id}")
async def delete_client(client_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Client).where(Client.id == client_id, Client.user_id == user.id))
    c = result.scalar_one_or_none()
    if not c: raise HTTPException(404, "Client not found")
    await db.delete(c)
    await db.commit()
    return {"success": True}
