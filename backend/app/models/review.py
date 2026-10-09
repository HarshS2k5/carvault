# Admin review queue and moderation action logs
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class ReviewQueue(Base, TimestampMixin):
    # Every single listing must enter this queue before public marketplace release
    __tablename__ = "review_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    listing_id = Column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), unique=True, nullable=False)
    assigned_admin_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Automated pre-review flags
    auto_check_phash_duplicate = Column(Boolean, default=False, nullable=False) # True if image reused from another seller
    auto_check_price_outlier = Column(Boolean, default=False, nullable=False)   # True if suspiciously far below market median
    auto_check_media_count_met = Column(Boolean, default=False, nullable=False) # Minimum 3 photos + 1 verification code shot
    auto_check_flags = Column(JSON, default=list, nullable=False)

    # Manual reviewer verification checklist
    checklist_code_matched = Column(Boolean, default=False, nullable=False)
    checklist_tamper_packaging_checked = Column(Boolean, default=False, nullable=False)
    checklist_media_clarity_checked = Column(Boolean, default=False, nullable=False)
    checklist_condition_matches_desc = Column(Boolean, default=False, nullable=False)

    reviewer_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    listing = relationship("Listing", back_populates="review_item", lazy="selectin")
    assigned_admin = relationship("User", lazy="selectin")
    actions = relationship("ReviewActionLog", back_populates="review_item", cascade="all, delete-orphan", lazy="selectin")

class ReviewActionLog(Base):
    # Immutable audit trail of every moderation decision taken
    __tablename__ = "review_action_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    review_queue_id = Column(String(36), ForeignKey("review_queue.id", ondelete="CASCADE"), nullable=False)
    admin_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    action = Column(String(50), nullable=False)  # 'APPROVE', 'REJECT', 'REQUEST_MORE_PROOF'
    reason = Column(Text, nullable=True)
    template_code = Column(String(50), nullable=True) # e.g. 'BLURRY_CARD', 'MISSING_VERIFICATION_TAG'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    review_item = relationship("ReviewQueue", back_populates="actions")
    admin = relationship("User")
