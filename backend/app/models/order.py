# Orders, shipping records, and state transition audit logs
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, BigInteger, Enum, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class OrderState(str, enum.Enum):
    CREATED = "CREATED"                      # Order created, awaiting buyer payment
    PAID_HELD = "PAID_HELD"                  # Payment captured by gateway split node, funds held in escrow
    SHIPPED = "SHIPPED"                      # Seller dispatched die-cast with courier waybill tracking
    DELIVERED = "DELIVERED"                  # Delivery confirmed via courier webhook or delivery OTP
    INSPECTION_WINDOW = "INSPECTION_WINDOW"  # 48-hour buyer inspection window active
    RELEASED = "RELEASED"                    # Funds settled to seller bank account; order complete
    DISPUTED = "DISPUTED"                    # Inspection claim raised (fake/damaged/wrong item); payout frozen
    REFUNDED = "REFUNDED"                    # Payment returned to buyer
    CANCELLED = "CANCELLED"                  # Order cancelled prior to dispatch

class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    listing_id = Column(String(36), ForeignKey("listings.id", ondelete="RESTRICT"), unique=True, nullable=False)
    buyer_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    seller_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    # Current lifecycle state (strictly modified only via state_machine service)
    current_state = Column(Enum(OrderState), default=OrderState.CREATED, nullable=False, index=True)

    # Financial figures in integer paise (₹1.00 = 100 paise)
    item_price_paise = Column(BigInteger, nullable=False)
    shipping_fee_paise = Column(BigInteger, default=0, nullable=False)
    
    # Platform commission structure
    commission_rate_bps = Column(Integer, nullable=False)       # e.g., 300 = 3.0% in beta
    commission_paise = Column(BigInteger, nullable=False)       # Calculated commission in paise
    min_platform_fee_paise = Column(BigInteger, default=2500, nullable=False) # ₹25 minimum platform fee
    gateway_fee_paise = Column(BigInteger, default=0, nullable=False)

    # Final split figures
    seller_payable_paise = Column(BigInteger, nullable=False)   # (item_price + shipping - commission)
    total_buyer_paid_paise = Column(BigInteger, nullable=False) # (item_price + shipping)

    # Licensed Gateway reference identifiers
    gateway_order_id = Column(String(100), unique=True, nullable=True)     # e.g. "order_rzp_12345"
    gateway_payment_id = Column(String(100), nullable=True)                # e.g. "pay_rzp_67890"
    gateway_transfer_id = Column(String(100), nullable=True)               # Marketplace split transfer ID

    # Delivery verification & window timestamps
    delivery_otp_hash = Column(String(128), nullable=True)
    inspection_window_ends_at = Column(DateTime, nullable=True)
    released_at = Column(DateTime, nullable=True)
    refunded_at = Column(DateTime, nullable=True)

    # Relationships configured with lazy="selectin" for safe async operations
    listing = relationship("Listing", lazy="selectin")
    buyer = relationship("User", foreign_keys=[buyer_id], lazy="selectin")
    seller = relationship("User", foreign_keys=[seller_id], lazy="selectin")
    transitions = relationship("OrderStateTransition", back_populates="order", cascade="all, delete-orphan", lazy="selectin")
    shipping = relationship("ShippingRecord", back_populates="order", uselist=False, cascade="all, delete-orphan", lazy="selectin")

class OrderStateTransition(Base):
    # Immutable audit record of EVERY state change in the escrow lifecycle
    __tablename__ = "order_state_transitions"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    from_state = Column(Enum(OrderState), nullable=False)
    to_state = Column(Enum(OrderState), nullable=False)
    triggered_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    trigger_source = Column(String(50), nullable=False)  # 'BUYER', 'SELLER', 'ADMIN', 'SYSTEM_TIMER', 'WEBHOOK'
    transition_metadata = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    order = relationship("Order", back_populates="transitions")
    actor = relationship("User", lazy="selectin")

class ShippingRecord(Base, TimestampMixin):
    # Courier tracking, packing proof video, and delivery confirmation
    __tablename__ = "shipping_records"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False)
    courier_partner = Column(String(50), default="DELHIVERY", nullable=False) # 'DELHIVERY', 'SHIPROCKET'
    tracking_id = Column(String(100), nullable=True)
    seller_packing_video_url = Column(Text, nullable=True)
    buyer_unboxing_video_url = Column(Text, nullable=True)
    status = Column(String(50), default="LABEL_GENERATED", nullable=False)
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="shipping")
