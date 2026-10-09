# Immutable double-entry ledger models in integer paise (₹1.00 = 100 paise)
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Enum, ForeignKey, Text, JSON, DateTime, Date, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class LedgerAccountType(str, enum.Enum):
    ASSET = "ASSET"          # Resources held (e.g. Gateway nodal escrow balance)
    LIABILITY = "LIABILITY"  # Obligations owed (e.g. Buyer held funds, Seller payable)
    EQUITY = "EQUITY"        # Retained capital
    REVENUE = "REVENUE"      # Platform commissions earned
    EXPENSE = "EXPENSE"      # Gateway gateway charges & write-offs

class EntryDirection(str, enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"

class LedgerAccount(Base, TimestampMixin):
    # Chart of accounts
    __tablename__ = "ledger_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    code = Column(String(60), unique=True, index=True, nullable=False) # e.g. 'ASSET_ESCROW_NODAL', 'LIABILITY_BUYER_FUNDS_HELD'
    name = Column(String(120), nullable=False)
    account_type = Column(Enum(LedgerAccountType), nullable=False)
    currency = Column(String(3), default="INR", nullable=False)

    entries = relationship("LedgerEntry", back_populates="account", lazy="selectin")

class LedgerTransaction(Base):
    # Groups balanced journal entry legs for a single financial event
    __tablename__ = "ledger_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    transaction_type = Column(String(60), index=True, nullable=False) # 'ORDER_PAYMENT_CAPTURED', 'ESCROW_PAYOUT_RELEASE', 'ORDER_REFUND'
    reference_id = Column(String(100), nullable=True)                 # Gateway payment_id or transfer_id
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    entries = relationship("LedgerEntry", back_populates="transaction", cascade="all, delete-orphan", lazy="selectin")
    order = relationship("Order", lazy="selectin")

class LedgerEntry(Base):
    # Individual debit or credit leg of a double-entry transaction
    __tablename__ = "ledger_entries"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    transaction_id = Column(String(36), ForeignKey("ledger_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    account_id = Column(String(36), ForeignKey("ledger_accounts.id", ondelete="RESTRICT"), nullable=False, index=True)
    direction = Column(Enum(EntryDirection), nullable=False)
    amount_paise = Column(BigInteger, nullable=False) # Integer paise (always strictly > 0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    transaction = relationship("LedgerTransaction", back_populates="entries")
    account = relationship("LedgerAccount", back_populates="entries", lazy="selectin")

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="chk_ledger_amount_positive"),
    )

class DailyReconciliation(Base):
    # Daily settlement comparison report against gateway settlement reports
    __tablename__ = "daily_reconciliations"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    recon_date = Column(Date, unique=True, index=True, nullable=False)
    gateway_total_paise = Column(BigInteger, nullable=False)
    ledger_total_paise = Column(BigInteger, nullable=False)
    discrepancy_paise = Column(BigInteger, nullable=False)
    status = Column(String(30), nullable=False) # 'MATCHED', 'MISMATCH_FLAGGED'
    mismatches = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
