# Die-cast listings, media verification, and catalog reference models
import enum
from sqlalchemy import Column, String, Integer, BigInteger, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import TimestampMixin, generate_uuid_str

class ListingCondition(str, enum.Enum):
    MINT_CARD = "MINT_CARD"        # Blister card intact with sharp corners, uncreased
    NEAR_MINT = "NEAR_MINT"        # Minor shelf wear on card/blister
    LOOSE_MINT = "LOOSE_MINT"      # Uncarded/loose car in pristine condition without paint chips
    PLAY_WORN = "PLAY_WORN"        # Signs of handling, play wear, or axle wobble
    CUSTOM = "CUSTOM"              # Modified wheels, decals, or custom chassis

class ListingStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"          # Live on marketplace
    REJECTED = "REJECTED"          # Failed physical or duplicate verification
    ACTION_REQUIRED = "ACTION_REQUIRED" # Admin asked for clearer baseplate/blister photo
    SOLD = "SOLD"
    DELISTED = "DELISTED"

class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    seller_id = Column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title = Column(String(200), index=True, nullable=False)
    description = Column(Text, nullable=False)
    series_name = Column(String(100), index=True, nullable=False)  # e.g. "Mainlines", "Car Culture", "Boulevard"
    model_year = Column(Integer, index=True, nullable=False)
    toy_code = Column(String(50), index=True, nullable=True)        # Casting / toy code e.g. "HKC34"
    condition = Column(Enum(ListingCondition), nullable=False)
    tags = Column(JSON, default=list, nullable=False)               # List of tags: ORIGINAL, CUSTOM, REPAINT, OPENED, SEALED
    price_paise = Column(BigInteger, nullable=False)               # Integer paise (e.g. ₹500.00 = 50000 paise)
    
    # Generated random physical verification code that must appear handwritten on paper next to car
    verification_code = Column(String(12), nullable=False)
    
    # True if captured directly via mobile in-app camera (required for high-value items)
    is_in_app_capture = Column(Boolean, default=False, nullable=False)
    
    status = Column(Enum(ListingStatus), default=ListingStatus.PENDING_REVIEW, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    view_count = Column(Integer, default=0, nullable=False)

    # Relationships configured with lazy="selectin" for safe async loading
    seller = relationship("User", back_populates="listings", lazy="selectin")
    media = relationship("ListingMedia", back_populates="listing", cascade="all, delete-orphan", lazy="selectin")
    review_item = relationship("ReviewQueue", back_populates="listing", uselist=False, cascade="all, delete-orphan", lazy="selectin")

class ListingMedia(Base, TimestampMixin):
    __tablename__ = "listing_media"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    listing_id = Column(String(36), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)
    media_url = Column(Text, nullable=False)
    media_type = Column(String(20), default="IMAGE", nullable=False)  # 'IMAGE' or 'VIDEO'
    
    # Flags whether this specific photo shows the car alongside the handwritten verification code
    is_verification_shot = Column(Boolean, default=False, nullable=False)
    
    # 64-bit perceptual hash (pHash) string to detect re-used photos across different sellers
    phash_value = Column(String(64), index=True, nullable=True)
    display_order = Column(Integer, default=0, nullable=False)

    listing = relationship("Listing", back_populates="media")

class DiecastCatalog(Base, TimestampMixin):
    # Benchmark reference pricing and casting metadata
    __tablename__ = "diecast_catalog"

    id = Column(String(36), primary_key=True, default=generate_uuid_str)
    series_name = Column(String(100), index=True, nullable=False)
    model_name = Column(String(150), index=True, nullable=False)
    release_year = Column(Integer, nullable=False)
    toy_code = Column(String(50), unique=True, index=True, nullable=True)
    estimated_mrp_paise = Column(BigInteger, nullable=True)
    typical_market_min_paise = Column(BigInteger, nullable=True)
    typical_market_max_paise = Column(BigInteger, nullable=True)
