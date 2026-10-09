# Admin Double-Entry Ledger and Settlement Reconciliation API endpoints
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.ledger import LedgerTransaction, DailyReconciliation
from app.services.ledger_service import get_account_balances
from app.services.reconciliation_service import run_daily_settlement_reconciliation

router = APIRouter()

class RunReconciliationRequest(BaseModel):
    recon_date: date
    gateway_reported_settlements: list = []

@router.get("/accounts/balances")
async def get_ledger_balances(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Returns net integer paise and rupee balances for all system accounts
    balances = await get_account_balances(db)
    return {
        "balances": balances,
        "escrow_held_paise": next((b["net_balance_paise"] for b in balances if b["account_code"] == "LIABILITY_BUYER_FUNDS_HELD"), 0),
        "seller_payable_paise": next((b["net_balance_paise"] for b in balances if b["account_code"] == "LIABILITY_SELLER_PAYABLE"), 0),
        "commission_earned_paise": next((b["net_balance_paise"] for b in balances if b["account_code"] == "REVENUE_PLATFORM_COMMISSION"), 0),
    }

@router.get("/transactions")
async def list_ledger_transactions(
    limit: int = Query(50, le=100),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Returns immutable double-entry journal logs with balanced entry legs
    stmt = (
        select(LedgerTransaction)
        .options(
            selectinload(LedgerTransaction.entries)
        )
        .order_by(LedgerTransaction.created_at.desc())
        .limit(limit)
    )
    res = await db.execute(stmt)
    transactions = res.scalars().all()
    
    return [
        {
            "id": tx.id,
            "order_id": tx.order_id,
            "transaction_type": tx.transaction_type,
            "reference_id": tx.reference_id,
            "description": tx.description,
            "created_at": tx.created_at,
            "entries": [
                {
                    "id": e.id,
                    "direction": e.direction.value,
                    "amount_paise": e.amount_paise,
                    "amount_rupees": e.amount_paise / 100.0,
                    "account_code": e.account.code if e.account else None,
                    "account_name": e.account.name if e.account else None,
                }
                for e in tx.entries
            ]
        }
        for tx in transactions
    ]

@router.post("/reconciliation/run")
async def run_reconciliation(
    payload: RunReconciliationRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Performs automated comparison of gateway settlement report vs platform ledger
    recon = await run_daily_settlement_reconciliation(
        recon_date=payload.recon_date,
        gateway_reported_settlements=payload.gateway_reported_settlements,
        db=db
    )
    return {
        "recon_date": str(recon.recon_date),
        "status": recon.status,
        "gateway_total_paise": recon.gateway_total_paise,
        "ledger_total_paise": recon.ledger_total_paise,
        "discrepancy_paise": recon.discrepancy_paise,
        "mismatches": recon.mismatches
    }

@router.get("/reconciliations")
async def list_reconciliations(
    limit: int = 30,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Retrieves history of daily settlement reconciliations
    stmt = select(DailyReconciliation).order_by(DailyReconciliation.recon_date.desc()).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
