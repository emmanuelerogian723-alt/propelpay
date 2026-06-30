"""Project Tracker API — with image upload support"""
import base64, uuid, os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.project import Project, ProjectUpdate
from app.models.client import Client
from app.services.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


def _pdict(p: Project, client_name: str = None) -> dict:
    return {
        "id": p.id, "name": p.name, "description": p.description,
        "status": p.status, "budget": p.budget, "currency": p.currency,
        "deadline": p.deadline, "progress": p.progress,
        "cover_image": p.cover_image, "tags": p.tags,
        "client_id": p.client_id, "client_name": client_name,
        "invoice_id": p.invoice_id, "notes": p.notes,
        "created_at": str(p.created_at), "updated_at": str(p.updated_at)
    }


class ProjectReq(BaseModel):
    name: str
    description: Optional[str] = None
    client_id: Optional[str] = None
    status: str = "active"
    budget: float = 0
    currency: str = "NGN"
    deadline: Optional[str] = None
    progress: float = 0
    tags: Optional[str] = None
    notes: Optional[str] = None
    cover_image: Optional[str] = None  # base64 data URL


class UpdateReq(BaseModel):
    note: str
    progress: Optional[float] = None
    image_url: Optional[str] = None  # base64 data URL


@router.get("")
async def list_projects(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    q = select(Project).where(Project.user_id == user.id)
    if status:
        q = q.where(Project.status == status)
    res = await db.execute(q.order_by(Project.created_at.desc()))
    projects = res.scalars().all()
    # batch load clients
    cids = list({p.client_id for p in projects if p.client_id})
    clients = {}
    if cids:
        cr = await db.execute(select(Client).where(Client.id.in_(cids)))
        for c in cr.scalars().all(): clients[c.id] = c
    return [_pdict(p, clients.get(p.client_id, {}) and clients.get(p.client_id).name) for p in projects]


@router.post("")
async def create_project(
    body: ProjectReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    p = Project(
        user_id=user.id, name=body.name, description=body.description,
        client_id=body.client_id, status=body.status, budget=body.budget,
        currency=body.currency, deadline=body.deadline, progress=body.progress,
        tags=body.tags, notes=body.notes, cover_image=body.cover_image
    )
    db.add(p); await db.commit(); await db.refresh(p)
    return _pdict(p)


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p: raise HTTPException(404, "Project not found")
    client = None
    if p.client_id:
        cr = await db.execute(select(Client).where(Client.id == p.client_id))
        client = cr.scalar_one_or_none()
    # Get updates
    ur = await db.execute(select(ProjectUpdate).where(ProjectUpdate.project_id == project_id).order_by(ProjectUpdate.created_at.desc()))
    updates = ur.scalars().all()
    return {
        **_pdict(p, client.name if client else None),
        "updates": [{"id":u.id,"note":u.note,"image_url":u.image_url,"progress":u.progress,"created_at":str(u.created_at)} for u in updates]
    }


@router.put("/{project_id}")
async def update_project(
    project_id: str,
    body: ProjectReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p: raise HTTPException(404, "Not found")
    for k, v in body.dict(exclude_unset=True).items():
        setattr(p, k, v)
    p.updated_at = datetime.utcnow()
    await db.commit(); await db.refresh(p)
    return _pdict(p)


@router.patch("/{project_id}/progress")
async def update_progress(
    project_id: str,
    progress: float,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p: raise HTTPException(404, "Not found")
    p.progress = max(0, min(100, progress))
    if p.progress >= 100: p.status = "completed"
    p.updated_at = datetime.utcnow()
    await db.commit()
    return {"success": True, "progress": p.progress, "status": p.status}


@router.post("/{project_id}/updates")
async def add_update(
    project_id: str,
    body: UpdateReq,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p: raise HTTPException(404, "Not found")
    u = ProjectUpdate(project_id=project_id, user_id=user.id, note=body.note,
                      image_url=body.image_url, progress=body.progress)
    db.add(u)
    if body.progress is not None:
        p.progress = max(0, min(100, body.progress))
        if p.progress >= 100: p.status = "completed"
        p.updated_at = datetime.utcnow()
    await db.commit(); await db.refresh(u)
    return {"id": u.id, "note": u.note, "image_url": u.image_url, "progress": u.progress, "created_at": str(u.created_at)}


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
    p = res.scalar_one_or_none()
    if not p: raise HTTPException(404, "Not found")
    await db.delete(p); await db.commit()
    return {"success": True}
