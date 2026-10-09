# Admin Review Queue API endpoints for human verification of all listings
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.schemas.review import (
    ReviewQueueItemResponse,
    ReviewApproveRequest,
    ReviewRejectRequest,
    ReviewRequestProofRequest
)
from app.schemas.listing import ListingResponse
from app.services.review_service import (
    get_pending_reviews,
    approve_listing,
    reject_listing,
    request_additional_proof
)

router = APIRouter()

@router.get("", response_model=List[ReviewQueueItemResponse])
async def list_pending_review_queue(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Displays queue of unapproved listings with automated fraud checks
    items = await get_pending_reviews(db)
    response_list = []
    for item in items:
        listing = item.listing
        listing_dto = ListingResponse(
            id=listing.id,
            seller_id=listing.seller_id,
            title=listing.title,
            description=listing.description,
            series_name=listing.series_name,
            model_year=listing.model_year,
            toy_code=listing.toy_code,
            condition=listing.condition,
            tags=listing.tags,
            price_paise=listing.price_paise,
            price_rupees=listing.price_paise / 100.0,
            verification_code=listing.verification_code,
            is_in_app_capture=listing.is_in_app_capture,
            status=listing.status,
            created_at=listing.created_at,
            media=listing.media
        )
        response_list.append(
            ReviewQueueItemResponse(
                id=item.id,
                listing_id=item.listing_id,
                auto_check_phash_duplicate=item.auto_check_phash_duplicate,
                auto_check_price_outlier=item.auto_check_price_outlier,
                auto_check_media_count_met=item.auto_check_media_count_met,
                auto_check_flags=item.auto_check_flags or [],
                checklist_code_matched=item.checklist_code_matched,
                checklist_tamper_packaging_checked=item.checklist_tamper_packaging_checked,
                checklist_media_clarity_checked=item.checklist_media_clarity_checked,
                checklist_condition_matches_desc=item.checklist_condition_matches_desc,
                reviewer_notes=item.reviewer_notes,
                submitted_at=item.submitted_at,
                listing=listing_dto
            )
        )
    return response_list

@router.post("/{review_id}/approve")
async def approve_review_item(
    review_id: str,
    payload: ReviewApproveRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Approves listing to publish it to marketplace search
    listing = await approve_listing(
        review_id=review_id,
        admin_id=current_admin.id,
        approve_data=payload,
        db=db
    )
    return {
        "status": "APPROVED",
        "listing_id": listing.id,
        "message": "Listing successfully approved and published live"
    }

@router.post("/{review_id}/reject")
async def reject_review_item(
    review_id: str,
    payload: ReviewRejectRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Rejects listing with standardized reason code
    listing = await reject_listing(
        review_id=review_id,
        admin_id=current_admin.id,
        reject_data=payload,
        db=db
    )
    return {
        "status": "REJECTED",
        "listing_id": listing.id,
        "message": "Listing rejected and removed from review queue"
    }

@router.post("/{review_id}/request-proof")
async def request_proof_review_item(
    review_id: str,
    payload: ReviewRequestProofRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Requests clearer physical evidence from seller
    listing = await request_additional_proof(
        review_id=review_id,
        admin_id=current_admin.id,
        proof_data=payload,
        db=db
    )
    return {
        "status": "ACTION_REQUIRED",
        "listing_id": listing.id,
        "message": "Notification dispatched to seller requesting additional proof"
    }
