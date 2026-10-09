# Base declarative models and shared mixins
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from app.core.database import Base

def generate_uuid_str() -> str:
    # Generates standard UUID4 string for portable primary keys across SQLite and Postgres
    return str(uuid.uuid4())

class TimestampMixin:
    # Auto-populates creation and update timestamps in UTC
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
