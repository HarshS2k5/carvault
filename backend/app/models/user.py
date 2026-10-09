# User, KYC verification, trust scores, and device tracking models
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Float, DateTime, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class UserRole(str, enum.Enum):
    BUYER = "BUYER"
    SELLER = "SELLER"
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER"

class KycTier(str, enum.Enum):
    TIER_0_NEW = "TIER_0_NEW"            # Default: strict listing caps, hold payouts
    TIER_1_VERIFIED = "TIER_1_VERIFIED"  # DigiLocker PAN + Penny drop verified
    TIER_2_PRO = "TIER_2_PRO"            # High volume trusted collector with proven track record

class KycStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    phone_number = Column(String(15), unique=True, index=True, nullable=False)
    full_name = Column(String(120), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.BUYER, nullable=False)
    kyc_tier = Column(Enum(KycTier), default=KycTier.TIER_0_NEW, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_banned = Column(Boolean, default=False, nullable=False)
    ban_reason = Column(Text, nullable=True)

    # Relationships configured with lazy="selectin" for safe async loading
    kyc_record = relationship("KycVerification", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    trust_score = relationship("UserTrustScore", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="selectin")
    listings = relationship("Listing", back_populates="seller")
    device_fingerprints = relationship("DeviceFingerprint", back_populates="user", cascade="all, delete-orphan", lazy="selectin")

class KycVerification(Base, TimestampMixin):
    # Compliant KYC audit trail. NEVER stores 12-digit Aadhaar numbers.
    # Uses DigiLocker transaction reference IDs and masked PAN identifiers.
    __tablename__ = "kyc_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    digilocker_request_id = Column(String(100), nullable=True)
    pan_number_masked = Column(String(10), nullable=True)  # e.g., "ABCDE****F"
    pan_name_matched = Column(Boolean, default=False)
    bank_account_masked = Column(String(20), nullable=True)
    bank_ifsc = Column(String(11), nullable=True)
    bank_penny_drop_name = Column(String(120), nullable=True)
    penny_drop_name_match_score = Column(Float, default=0.0)  # Percentage confidence
    selfie_liveness_score = Column(Float, default=0.0)
    status = Column(Enum(KycStatus), default=KycStatus.PENDING, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="kyc_record")

class UserTrustScore(Base):
    # Dynamic collector trust scoring engine
    __tablename__ = "user_trust_scores"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    score = Column(Integer, default=50, nullable=False)  # Scaled 0 to 100
    completed_orders = Column(Integer, default=0, nullable=False)
    dispute_count = Column(Integer, default=0, nullable=False)
    refund_count = Column(Integer, default=0, nullable=False)
    report_count = Column(Integer, default=0, nullable=False)
    active_listing_cap = Column(Integer, default=3, nullable=False)  # Caps active items for unverified/low trust
    payout_hold_hours = Column(Integer, default=48, nullable=False)
    risk_flags = Column(JSON, default=list, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="trust_score")

class DeviceFingerprint(Base):
    # Device and IP tracking for anti-sybil and ban enforcement
    __tablename__ = "device_fingerprints"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_hash = Column(String(64), index=True, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_blocked = Column(Boolean, default=False, nullable=False)
    last_seen_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="device_fingerprints")
