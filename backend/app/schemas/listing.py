# Pydantic schemas for listings, media attachments, and physical verification codes
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.models.listing import ListingCondition, ListingStatus

class VerificationCodeResponse(BaseModel):
    verification_code: str
    instructions: str = "Write this code clearly on paper and place it next to the car in your verification photo."
    expires_in_minutes: int = 60

class ListingMediaCreate(BaseModel):
    media_url: str
    media_type: str = "IMAGE"
    is_verification_shot: bool = False
    phash_value: Optional[str] = None
    display_order: int = 0

class ListingMediaResponse(BaseModel):
    id: str
    media_url: str
    media_type: str
    is_verification_shot: bool
    display_order: int

    model_config = ConfigDict(from_attributes=True)

class ListingCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    series_name: str = Field(..., max_length=100, description="e.g. Mainline, Car Culture, Boulevard")
    model_year: int = Field(..., ge=1968, le=2028)
    toy_code: Optional[str] = Field(None, max_length=50)
    condition: ListingCondition
    tags: List[str] = Field(default_factory=list, description="ORIGINAL, CUSTOM, REPAINT, OPENED, SEALED")
    price_paise: int = Field(..., gt=0, description="Price in integer paise (₹500 = 50000 paise)")
    verification_code: str = Field(..., min_length=6, max_length=12)
    is_in_app_capture: bool = False
    media: List[ListingMediaCreate] = Field(..., min_length=1)

class ListingResponse(BaseModel):
    id: str
    seller_id: str
    title: str
    description: str
    series_name: str
    model_year: int
    toy_code: Optional[str]
    condition: ListingCondition
    tags: List[str]
    price_paise: int
    price_rupees: float
    verification_code: str
    is_in_app_capture: bool
    status: ListingStatus
    created_at: datetime
    media: List[ListingMediaResponse] = []

    model_config = ConfigDict(from_attributes=True)

class ListingDetailResponse(ListingResponse):
    seller_name: Optional[str] = None
    seller_kyc_tier: Optional[str] = None
    seller_trust_score: Optional[int] = None
