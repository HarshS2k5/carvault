# Payment transactions, idempotent webhook logs, and subaccount mappings
from datetime import datetime, timezone
from sqlalchemy import Column, String, BigInteger, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class PaymentTransaction(Base, TimestampMixin):
    # Records payments received through licensed gateway split product
    __tablename__ = "payment_transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="RESTRICT"), nullable=False, index=True)
    gateway_name = Column(String(50), default="RAZORPAY_ROUTE", nullable=False) # 'RAZORPAY_ROUTE', 'CASHFREE_SPLIT'
    gateway_payment_id = Column(String(100), unique=True, nullable=False, index=True)
    amount_paise = Column(BigInteger, nullable=False)
    currency = Column(String(3), default="INR", nullable=False)
    status = Column(String(50), default="CAPTURED", nullable=False) # 'CAPTURED', 'FAILED', 'REFUNDED'
    raw_payload = Column(JSON, default=dict, nullable=False)

    order = relationship("Order", lazy="selectin")

class GatewayWebhookLog(Base):
    # Idempotency log: ensures payment webhooks are never processed more than once
    __tablename__ = "gateway_webhook_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    event_id = Column(String(120), unique=True, nullable=False, index=True) # Gateway event ID e.g. "evt_123"
    event_type = Column(String(80), nullable=False)                         # e.g. "payment.captured", "order.paid"
    signature = Column(String(128), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

class SellerSubaccount(Base, TimestampMixin):
    # Maps platform sellers to gateway marketplace split accounts (never holds custody of funds)
    __tablename__ = "seller_subaccounts"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    gateway_account_id = Column(String(100), unique=True, nullable=False) # e.g. "acc_Hdfc382109"
    status = Column(String(30), default="ACTIVE", nullable=False)

    user = relationship("User", lazy="selectin")
