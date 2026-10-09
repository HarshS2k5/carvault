# User reporting and anti-fraud enforcement models
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class ReportTarget(str, enum.Enum):
    LISTING = "LISTING"
    PROFILE = "PROFILE"
    CHAT = "CHAT"
    ORDER = "ORDER"

class ReportReason(str, enum.Enum):
    FAKE_ITEM = "FAKE_ITEM"                     # Counterfeit casting or fraudulent tampo
    FAKE_PHOTOS_VIDEO = "FAKE_PHOTOS_VIDEO"     # Stock photo or stolen image
    RESEALED_PACKAGING = "RESEALED_PACKAGING"   # Acetone/glued blister passed as factory mint
    OFF_PLATFORM_PAYMENT = "OFF_PLATFORM_PAYMENT" # Requesting direct UPI or bank transfer
    NOT_DELIVERED = "NOT_DELIVERED"
    IMPERSONATION = "IMPERSONATION"
    ILLEGAL_ITEM = "ILLEGAL_ITEM"
    FAKE_REVIEWS = "FAKE_REVIEWS"
    HARASSMENT = "HARASSMENT"
    OTHER = "OTHER"

class ReportPriority(str, enum.Enum):
    URGENT = "URGENT" # Fraud, fake item, off-platform payment (target 24h resolution)
    HIGH = "HIGH"
    NORMAL = "NORMAL"

class ReportStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_REVIEW = "IN_REVIEW"
    ACTION_TAKEN = "ACTION_TAKEN"
    DISMISSED = "DISMISSED"
    FALSE_REPORT_PENALIZED = "FALSE_REPORT_PENALIZED" # Bad faith report penalized

class UserReport(Base, TimestampMixin):
    __tablename__ = "user_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    reference_id = Column(String(30), unique=True, index=True, nullable=False) # e.g. "REP-2026-98124"
    reporter_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_type = Column(Enum(ReportTarget), nullable=False)
    target_id = Column(String(60), nullable=False, index=True)
    reason = Column(Enum(ReportReason), nullable=False, index=True)
    description = Column(Text, nullable=False)
    evidence_url = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True)
    priority = Column(Enum(ReportPriority), default=ReportPriority.NORMAL, nullable=False, index=True)
    status = Column(Enum(ReportStatus), default=ReportStatus.OPEN, nullable=False, index=True)
    assigned_admin_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_action = Column(String(60), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id], lazy="selectin")
    assigned_admin = relationship("User", foreign_keys=[assigned_admin_id], lazy="selectin")
