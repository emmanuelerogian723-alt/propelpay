"""Dashboard & Analytics endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from app.database import get_db
from app.models.user import User
from app.models.invoice import Invoice
from app.models.proposal import Proposal
from app.models.client import Client
from app.models.payment import Payment
from app.services.auth import get_current_user
from app.services.ai import ai_insights

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Invoice stats
    inv_res = await db.execute(select(Invoice).where(Invoice.user_id == user.id))
    invoices = inv_res.scalars().all()
    total_invoiced = sum(i.total for i in invoices)
    total_paid = sum(i.total for i in invoices if i.status == "paid")
    total_pending = sum(i.total for i in invoices if i.status in ("sent","viewed"))
    overdue = [i for i in invoices if i.status in ("sent","viewed","overdue") and i.due_date and
               date.fromisoformat(i.due_date) < date.today()]
    total_overdue = sum(i.total for i in overdue)

    # Proposals
    prop_res = await db.execute(select(Proposal).where(Proposal.user_id == user.id))
    proposals = prop_res.scalars().all()
    proposals_sent = len([p for p in proposals if p.status != "draft"])
    proposals_accepted = len([p for p in proposals if p.status == "accepted"])

    # Clients
    client_res = await db.execute(select(func.count(Client.id)).where(Client.user_id == user.id))
    client_count = client_res.scalar() or 0

    # Recent activity (last 6 months revenue)
    months = []
    for i in range(5, -1, -1):
        d = date.today().replace(day=1) - timedelta(days=i*30)
        month_str = d.strftime("%Y-%m")
        month_paid = sum(inv.total for inv in invoices if inv.status == "paid" and
                        str(inv.created_at)[:7] == month_str)
        months.append({"month": d.strftime("%b"), "revenue": month_paid})

    # Top client
    client_revenue = {}
    for inv in invoices:
        if inv.client_id and inv.status == "paid":
            client_revenue[inv.client_id] = client_revenue.get(inv.client_id, 0) + inv.total
    top_client_id = max(client_revenue, key=client_revenue.get) if client_revenue else None
    top_client_name = "N/A"
    if top_client_id:
        cr = await db.execute(select(Client).where(Client.id == top_client_id))
        tc = cr.scalar_one_or_none()
        if tc: top_client_name = tc.name

    return {
        "currency": user.currency,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "total_overdue": total_overdue,
        "collection_rate": round(total_paid / total_invoiced * 100, 1) if total_invoiced > 0 else 0,
        "overdue_count": len(overdue),
        "invoice_count": len(invoices),
        "proposals_sent": proposals_sent,
        "proposals_accepted": proposals_accepted,
        "proposal_close_rate": round(proposals_accepted / proposals_sent * 100, 1) if proposals_sent > 0 else 0,
        "client_count": client_count,
        "top_client": top_client_name,
        "monthly_revenue": months,
        "plan": user.plan,
    }

@router.get("/insights")
async def get_insights(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stats = await get_stats(user=user, db=db)
    insights = ai_insights(
        total_invoiced=stats["total_invoiced"],
        total_paid=stats["total_paid"],
        overdue_count=stats["overdue_count"],
        top_client=stats["top_client"],
        currency=user.currency
    )
    return {"insights": insights, "stats": stats}

@router.get("/recent")
async def recent_activity(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    inv_res = await db.execute(select(Invoice).where(Invoice.user_id == user.id).order_by(Invoice.created_at.desc()).limit(5))
    invoices = inv_res.scalars().all()
    prop_res = await db.execute(select(Proposal).where(Proposal.user_id == user.id).order_by(Proposal.created_at.desc()).limit(5))
    proposals = prop_res.scalars().all()
    
    activity = []
    for i in invoices:
        activity.append({"type": "invoice", "id": i.id, "title": f"Invoice {i.invoice_number}",
                         "amount": i.total, "currency": i.currency, "status": i.status,
                         "date": str(i.created_at)})
    for p in proposals:
        activity.append({"type": "proposal", "id": p.id, "title": p.title,
                         "amount": p.total_amount, "currency": p.currency, "status": p.status,
                         "date": str(p.created_at)})
    activity.sort(key=lambda x: x["date"], reverse=True)
    return activity[:10]
