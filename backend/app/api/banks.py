"""Multi-currency bank accounts API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.bank_account import BankAccount
from app.services.auth import get_current_user

router = APIRouter(prefix="/banks", tags=["banks"])

SUPPORTED_CURRENCIES = ["NGN", "USD", "GBP", "EUR", "GHS", "KES", "ZAR"]

class BankReq(BaseModel):
    currency: str
    bank_name: str
    account_number: str
    account_name: str
    bank_code: Optional[str] = None
    routing_number: Optional[str] = None
    swift_code: Optional[str] = None
    iban: Optional[str] = None
    is_primary: bool = False

def _bank_dict(b: BankAccount) -> dict:
    return {
        "id": b.id, "currency": b.currency, "bank_name": b.bank_name,
        "account_number": b.account_number[-4:].zfill(len(b.account_number)),  # mask
        "account_number_full": b.account_number,
        "account_name": b.account_name, "bank_code": b.bank_code,
        "routing_number": b.routing_number, "swift_code": b.swift_code,
        "iban": b.iban, "is_primary": b.is_primary, "is_active": b.is_active,
        "created_at": str(b.created_at),
    }

@router.get("")
async def list_banks(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(BankAccount).where(BankAccount.user_id == user.id, BankAccount.is_active == True)
        .order_by(BankAccount.is_primary.desc(), BankAccount.created_at.asc())
    )
    banks = result.scalars().all()
    # Group by currency
    by_currency = {}
    for b in banks:
        if b.currency not in by_currency:
            by_currency[b.currency] = []
        by_currency[b.currency].append(_bank_dict(b))
    return {"banks": [_bank_dict(b) for b in banks], "by_currency": by_currency}

@router.post("")
async def add_bank(body: BankReq, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if body.currency not in SUPPORTED_CURRENCIES:
        raise HTTPException(400, f"Currency must be one of: {', '.join(SUPPORTED_CURRENCIES)}")
    # If primary, demote others for same currency
    if body.is_primary:
        result = await db.execute(
            select(BankAccount).where(BankAccount.user_id == user.id,
                                      BankAccount.currency == body.currency))
        for b in result.scalars().all():
            b.is_primary = False
    bank = BankAccount(
        user_id=user.id, currency=body.currency, bank_name=body.bank_name,
        account_number=body.account_number, account_name=body.account_name,
        bank_code=body.bank_code, routing_number=body.routing_number,
        swift_code=body.swift_code, iban=body.iban, is_primary=body.is_primary
    )
    db.add(bank)
    await db.commit()
    await db.refresh(bank)
    return _bank_dict(bank)

@router.put("/{bank_id}")
async def update_bank(bank_id: str, data: dict,
                       user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BankAccount).where(BankAccount.id == bank_id,
                                                         BankAccount.user_id == user.id))
    bank = result.scalar_one_or_none()
    if not bank: raise HTTPException(404, "Bank account not found")
    allowed = ["bank_name","account_number","account_name","bank_code","routing_number","swift_code","iban","is_primary"]
    for k, v in data.items():
        if k in allowed: setattr(bank, k, v)
    if data.get("is_primary"):
        others = await db.execute(select(BankAccount).where(
            BankAccount.user_id == user.id, BankAccount.currency == bank.currency,
            BankAccount.id != bank_id))
        for b in others.scalars().all():
            b.is_primary = False
    await db.commit()
    return _bank_dict(bank)

@router.delete("/{bank_id}")
async def delete_bank(bank_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BankAccount).where(BankAccount.id == bank_id,
                                                         BankAccount.user_id == user.id))
    bank = result.scalar_one_or_none()
    if not bank: raise HTTPException(404, "Bank account not found")
    bank.is_active = False  # soft delete
    await db.commit()
    return {"success": True, "message": "Bank account removed"}

@router.get("/for-invoice/{invoice_id}")
async def get_bank_for_invoice(invoice_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Return the right bank account for an invoice's currency."""
    from app.models.invoice import Invoice
    inv_res = await db.execute(select(Invoice).where(Invoice.id == invoice_id, Invoice.user_id == user.id))
    inv = inv_res.scalar_one_or_none()
    if not inv: raise HTTPException(404, "Invoice not found")
    bank_res = await db.execute(select(BankAccount).where(
        BankAccount.user_id == user.id, BankAccount.currency == inv.currency,
        BankAccount.is_active == True).order_by(BankAccount.is_primary.desc()))
    bank = bank_res.scalars().first()
    return {"bank": _bank_dict(bank) if bank else None, "currency": inv.currency}
