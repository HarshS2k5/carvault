# Immutable double-entry ledger accounting service in integer paise
# Enforces the mathematical invariant: sum(DEBITS) == sum(CREDITS) on every transaction.
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.ledger import (
    LedgerAccount, LedgerAccountType, EntryDirection,
    LedgerTransaction, LedgerEntry
)
from app.models.order import Order

# Canonical system account definitions
STANDARD_ACCOUNTS = {
    "ASSET_ESCROW_NODAL": ("Gateway Nodal Escrow Account", LedgerAccountType.ASSET),
    "LIABILITY_BUYER_FUNDS_HELD": ("Buyer Funds Held In Escrow", LedgerAccountType.LIABILITY),
    "LIABILITY_SELLER_PAYABLE": ("Seller Payouts Payable", LedgerAccountType.LIABILITY),
    "REVENUE_PLATFORM_COMMISSION": ("Marketplace Commission Revenue", LedgerAccountType.REVENUE),
    "EXPENSE_GATEWAY_FEES": ("Payment Gateway Fees Expense", LedgerAccountType.EXPENSE),
}

class LedgerImbalanceError(Exception):
    # Raised when debits do not equal credits in a transaction
    pass

async def ensure_ledger_accounts_exist(db: AsyncSession) -> Dict[str, LedgerAccount]:
    # Seeds or retrieves canonical system chart of accounts
    accounts = {}
    for code, (name, acc_type) in STANDARD_ACCOUNTS.items():
        stmt = select(LedgerAccount).where(LedgerAccount.code == code)
        res = await db.execute(stmt)
        acc = res.scalars().first()
        if not acc:
            acc = LedgerAccount(code=code, name=name, account_type=acc_type, currency="INR")
            db.add(acc)
            await db.flush()
        accounts[code] = acc
    await db.commit()
    return accounts

async def record_balanced_transaction(
    order_id: str,
    transaction_type: str,
    reference_id: str,
    description: str,
    entries: List[dict], # [{"account_code": "...", "direction": EntryDirection, "amount_paise": 150000}]
    db: AsyncSession
) -> LedgerTransaction:
    # Invariant Enforcement: sum(debits) must strictly equal sum(credits)
    total_debit = sum(e["amount_paise"] for e in entries if e["direction"] == EntryDirection.DEBIT)
    total_credit = sum(e["amount_paise"] for e in entries if e["direction"] == EntryDirection.CREDIT)

    if total_debit != total_credit:
        raise LedgerImbalanceError(
            f"Double-entry ledger imbalance detected! Debits ({total_debit} paise) != Credits ({total_credit} paise)"
        )

    # Ensure accounts exist
    accounts = await ensure_ledger_accounts_exist(db)

    # Create root transaction
    tx = LedgerTransaction(
        order_id=order_id,
        transaction_type=transaction_type,
        reference_id=reference_id,
        description=description
    )
    db.add(tx)
    await db.flush()

    # Create balanced entry legs
    for e in entries:
        acc = accounts[e["account_code"]]
        entry = LedgerEntry(
            transaction_id=tx.id,
            account_id=acc.id,
            direction=e["direction"],
            amount_paise=e["amount_paise"]
        )
        db.add(entry)

    await db.commit()
    await db.refresh(tx)
    return tx

async def record_payment_captured_ledger(order: Order, gateway_payment_id: str, db: AsyncSession) -> LedgerTransaction:
    # 1. Buyer payment captured:
    # DEBIT:  ASSET_ESCROW_NODAL (Gateway holds buyer money)
    # CREDIT: LIABILITY_BUYER_FUNDS_HELD (Platform owes fulfillment or refund to buyer)
    entries = [
        {
            "account_code": "ASSET_ESCROW_NODAL",
            "direction": EntryDirection.DEBIT,
            "amount_paise": order.total_buyer_paid_paise
        },
        {
            "account_code": "LIABILITY_BUYER_FUNDS_HELD",
            "direction": EntryDirection.CREDIT,
            "amount_paise": order.total_buyer_paid_paise
        }
    ]
    return await record_balanced_transaction(
        order_id=order.id,
        transaction_type="ORDER_PAYMENT_CAPTURED",
        reference_id=gateway_payment_id,
        description=f"Payment captured for Order #{order.id[:8]} via Gateway",
        entries=entries,
        db=db
    )

async def record_escrow_payout_release_ledger(order: Order, db: AsyncSession) -> LedgerTransaction:
    # 2. Buyer inspection window passes; funds release to seller:
    # DEBIT:  LIABILITY_BUYER_FUNDS_HELD   (Total buyer paid)
    # CREDIT: LIABILITY_SELLER_PAYABLE     (Seller net payout)
    # CREDIT: REVENUE_PLATFORM_COMMISSION  (CarVault marketplace take-rate)
    entries = [
        {
            "account_code": "LIABILITY_BUYER_FUNDS_HELD",
            "direction": EntryDirection.DEBIT,
            "amount_paise": order.total_buyer_paid_paise
        },
        {
            "account_code": "LIABILITY_SELLER_PAYABLE",
            "direction": EntryDirection.CREDIT,
            "amount_paise": order.seller_payable_paise
        },
        {
            "account_code": "REVENUE_PLATFORM_COMMISSION",
            "direction": EntryDirection.CREDIT,
            "amount_paise": order.commission_paise
        }
    ]
    return await record_balanced_transaction(
        order_id=order.id,
        transaction_type="ESCROW_PAYOUT_RELEASE",
        reference_id=order.gateway_payment_id,
        description=f"Escrow release for Order #{order.id[:8]}: Payout ₹{order.seller_payable_paise/100:.2f}, Fee ₹{order.commission_paise/100:.2f}",
        entries=entries,
        db=db
    )

async def record_order_refund_ledger(order: Order, reference_id: str, db: AsyncSession) -> LedgerTransaction:
    # 3. Order refunded to buyer:
    # DEBIT:  LIABILITY_BUYER_FUNDS_HELD (Obligation removed)
    # CREDIT: ASSET_ESCROW_NODAL         (Cash returned from gateway nodal account)
    entries = [
        {
            "account_code": "LIABILITY_BUYER_FUNDS_HELD",
            "direction": EntryDirection.DEBIT,
            "amount_paise": order.total_buyer_paid_paise
        },
        {
            "account_code": "ASSET_ESCROW_NODAL",
            "direction": EntryDirection.CREDIT,
            "amount_paise": order.total_buyer_paid_paise
        }
    ]
    return await record_balanced_transaction(
        order_id=order.id,
        transaction_type="ORDER_REFUND",
        reference_id=reference_id,
        description=f"Refund issued for Order #{order.id[:8]}",
        entries=entries,
        db=db
    )

async def get_account_balances(db: AsyncSession) -> List[dict]:
    # Calculates the exact net balance of every ledger account using direct SQL sums
    await ensure_ledger_accounts_exist(db)
    stmt = select(LedgerAccount).order_by(LedgerAccount.code)
    res = await db.execute(stmt)
    accounts = res.scalars().all()

    balances = []
    for acc in accounts:
        # Aggregate debits
        debit_stmt = select(func.coalesce(func.sum(LedgerEntry.amount_paise), 0)).where(
            LedgerEntry.account_id == acc.id,
            LedgerEntry.direction == EntryDirection.DEBIT
        )
        debit_res = await db.execute(debit_stmt)
        debit_sum = debit_res.scalar_one()

        # Aggregate credits
        credit_stmt = select(func.coalesce(func.sum(LedgerEntry.amount_paise), 0)).where(
            LedgerEntry.account_id == acc.id,
            LedgerEntry.direction == EntryDirection.CREDIT
        )
        credit_res = await db.execute(credit_stmt)
        credit_sum = credit_res.scalar_one()

        # Asset & Expense have normal DEBIT balance; Liabilities, Equity & Revenue have normal CREDIT balance
        if acc.account_type in [LedgerAccountType.ASSET, LedgerAccountType.EXPENSE]:
            net_balance_paise = debit_sum - credit_sum
        else:
            net_balance_paise = credit_sum - debit_sum

        balances.append({
            "account_code": acc.code,
            "account_name": acc.name,
            "account_type": acc.account_type.value,
            "net_balance_paise": net_balance_paise,
            "net_balance_rupees": net_balance_paise / 100.0,
            "total_debit_paise": debit_sum,
            "total_credit_paise": credit_sum
        })
    return balances
