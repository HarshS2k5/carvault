# Disputes and evidence collation models for escrow claim resolution
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class DisputeStatus(str, enum.Enum):
    OPENED = "OPENED"
    EVIDENCE_SUBMITTED = "EVIDENCE_SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    RESOLVED_RELEASED = "RESOLVED_RELEASED" # Admin sided with seller (funds released)
    RESOLVED_REFUNDED = "RESOLVED_REFUNDED" # Admin sided with buyer (funds refunded)

class Dispute(Base, TimestampMixin):
    __tablename__ = "disputes"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    order_id = Column(String(36), ForeignKey("orders.id", ondelete="RESTRICT"), unique=True, nullable=False, index=True)
    raised_by_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(DisputeStatus), default=DisputeStatus.OPENED, nullable=False, index=True)
    admin_notes = Column(Text, nullable=True)
    resolved_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolution_action = Column(String(50), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("Order", lazy="selectin")
    raised_by = relationship("User", foreign_keys=[raised_by_id], lazy="selectin")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], lazy="selectin")
    evidence = relationship("DisputeEvidence", back_populates="dispute", cascade="all, delete-orphan", lazy="selectin")

class DisputeEvidence(Base):
    # Supporting evidence uploaded by buyer (unboxing video) or seller (packing video)
    __tablename__ = "dispute_evidence"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    dispute_id = Column(String(36), ForeignKey("disputes.id", ondelete="CASCADE"), nullable=False, index=True)
    uploader_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    uploader_role = Column(String(20), nullable=False) # 'BUYER' or 'SELLER'
    file_url = Column(Text, nullable=False)
    file_type = Column(String(20), default="VIDEO", nullable=False) # 'VIDEO' or 'IMAGE'
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    dispute = relationship("Dispute", back_populates="evidence")
    uploader = relationship("User", lazy="selectin")
