# Platform security and regulatory audit log
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from app.core.database import Base
from app.models.base import generate_uuid_str

class SystemAuditLog(Base):
    # Logs critical events (admin actions, state transitions, KYC status changes, bans)
    __tablename__ = "system_audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(60), index=True, nullable=False) # e.g. "KYC_VERIFIED", "LISTING_APPROVED", "USER_BANNED"
    resource_type = Column(String(60), nullable=False)           # e.g. "USER", "LISTING", "ORDER"
    resource_id = Column(String(60), nullable=False)
    ip_address = Column(String(45), nullable=True)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
