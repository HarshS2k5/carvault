# Pydantic schemas for Admin Review Queue and moderation decisions
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime
from app.schemas.listing import ListingResponse

class ReviewChecklistUpdate(BaseModel):
    checklist_code_matched: bool
    checklist_tamper_packaging_checked: bool
    checklist_media_clarity_checked: bool
    checklist_condition_matches_desc: bool

class ReviewApproveRequest(BaseModel):
    reviewer_notes: Optional[str] = "Listing verified and approved for marketplace"
    checklist: ReviewChecklistUpdate

class ReviewRejectRequest(BaseModel):
    template_code: str = Field(..., description="e.g. FAKE_PHOTOS, REUSED_IMAGE, BLURRY_MEDIA, TAMPERED_CARD")
    rejection_reason: str = Field(..., min_length=5)

class ReviewRequestProofRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Instructions to seller for additional proof required")
    required_shots: List[str] = ["Baseplate casting code closeup", "Corner wear closeup"]

class ReviewQueueItemResponse(BaseModel):
    id: str
    listing_id: str
    auto_check_phash_duplicate: bool
    auto_check_price_outlier: bool
    auto_check_media_count_met: bool
    auto_check_flags: List[str]
    checklist_code_matched: bool
    checklist_tamper_packaging_checked: bool
    checklist_media_clarity_checked: bool
    checklist_condition_matches_desc: bool
    reviewer_notes: Optional[str]
    submitted_at: datetime
    listing: ListingResponse

    model_config = ConfigDict(from_attributes=True)
