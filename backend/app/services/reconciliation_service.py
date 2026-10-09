# Daily gateway reconciliation engine comparing internal double-entry ledger with gateway settlements
from datetime import date, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.ledger import DailyReconciliation, LedgerTransaction, LedgerEntry, LedgerAccount, EntryDirection

async def run_daily_settlement_reconciliation(
    recon_date: date,
    gateway_reported_settlements: list, # [{"order_id": "...", "gateway_amount_paise": 150000, "payment_id": "..."}]
    db: AsyncSession
) -> DailyReconciliation:
    # 1. Compute gateway reported total in integer paise
    gateway_total_paise = sum(item["gateway_amount_paise"] for item in gateway_reported_settlements)

    # 2. Compute internal platform ledger captured volume for target date
    # Query transactions of type ORDER_PAYMENT_CAPTURED created on that date
    date_str = recon_date.isoformat() if hasattr(recon_date, "isoformat") else str(recon_date)

    stmt = (
        select(func.coalesce(func.sum(LedgerEntry.amount_paise), 0))
        .select_from(LedgerEntry)
        .join(LedgerTransaction, LedgerEntry.transaction_id == LedgerTransaction.id)
        .join(LedgerAccount, LedgerEntry.account_id == LedgerAccount.id)
        .where(
            LedgerTransaction.transaction_type == "ORDER_PAYMENT_CAPTURED",
            LedgerAccount.code == "ASSET_ESCROW_NODAL",
            LedgerEntry.direction == EntryDirection.DEBIT,
            func.date(LedgerTransaction.created_at) == date_str
        )
    )
    res = await db.execute(stmt)
    ledger_total_paise = res.scalar_one()

    # 3. Detect any itemized mismatches
    discrepancy_paise = gateway_total_paise - ledger_total_paise
    mismatches = []

    if discrepancy_paise != 0:
        mismatches.append({
            "issue": "SETTLEMENT_TOTAL_DISCREPANCY",
            "gateway_total_paise": gateway_total_paise,
            "ledger_total_paise": ledger_total_paise,
            "discrepancy_paise": discrepancy_paise,
            "description": f"Mismatch of INR {abs(discrepancy_paise)/100:.2f} between gateway report and CarVault ledger"
        })

    status = "MATCHED" if discrepancy_paise == 0 else "MISMATCH_FLAGGED"

    # 4. Check if a report for this date already exists
    existing_stmt = select(DailyReconciliation).where(DailyReconciliation.recon_date == recon_date)
    existing_res = await db.execute(existing_stmt)
    recon_record = existing_res.scalars().first()

    if not recon_record:
        recon_record = DailyReconciliation(
            recon_date=recon_date,
            gateway_total_paise=gateway_total_paise,
            ledger_total_paise=ledger_total_paise,
            discrepancy_paise=discrepancy_paise,
            status=status,
            mismatches=mismatches
        )
        db.add(recon_record)
    else:
        recon_record.gateway_total_paise = gateway_total_paise
        recon_record.ledger_total_paise = ledger_total_paise
        recon_record.discrepancy_paise = discrepancy_paise
        recon_record.status = status
        recon_record.mismatches = mismatches

    await db.commit()
    await db.refresh(recon_record)
    return recon_record
