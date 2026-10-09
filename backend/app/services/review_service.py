# Review queue service governing manual verification checklist and moderation decisions
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.listing import Listing, ListingStatus
from app.models.review import ReviewQueue, ReviewActionLog
from app.models.audit import SystemAuditLog

async def get_pending_reviews(db: AsyncSession, limit=50):
    # Returns items currently pending admin approval with eagerly loaded listing and media
    stmt = (
        select(ReviewQueue)
        .join(Listing)
        .where(Listing.status == ListingStatus.PENDING_REVIEW)
        .options(
            selectinload(ReviewQueue.listing).selectinload(Listing.media)
        )
        .order_by(ReviewQueue.submitted_at.asc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

async def approve_listing(review_id, admin_id, approve_data, db: AsyncSession):
    # Approves listing only when physical verification checklist has been fulfilled
    review = await db.get(ReviewQueue, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    listing = await db.get(Listing, review.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Associated listing not found")

    # Enforce checklist criteria: verification code must be confirmed by reviewer
    if not approve_data.checklist.checklist_code_matched:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot approve: verification code match must be confirmed."
        )

    # Update checklist status
    review.checklist_code_matched = approve_data.checklist.checklist_code_matched
    review.checklist_tamper_packaging_checked = approve_data.checklist.checklist_tamper_packaging_checked
    review.checklist_media_clarity_checked = approve_data.checklist.checklist_media_clarity_checked
    review.checklist_condition_matches_desc = approve_data.checklist.checklist_condition_matches_desc
    review.reviewer_notes = approve_data.reviewer_notes
    review.assigned_admin_id = admin_id
    review.reviewed_at = datetime.now(timezone.utc)

    # Publish listing live on marketplace
    listing.status = ListingStatus.APPROVED

    # Create immutable action log
    action_log = ReviewActionLog(
        review_queue_id=review.id,
        admin_id=admin_id,
        action="APPROVE",
        reason=approve_data.reviewer_notes or "Passed all verification checks",
        template_code="APPROVED_PHYSICAL_MATCH"
    )
    db.add(action_log)

    # Compliance audit log
    audit_entry = SystemAuditLog(
        actor_id=admin_id,
        action_type="LISTING_APPROVED",
        resource_type="LISTING",
        resource_id=listing.id,
        details={"notes": approve_data.reviewer_notes}
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(listing)
    return listing

async def reject_listing(review_id, admin_id, reject_data, db: AsyncSession):
    # Rejects listing with standardized template code and customer explanation
    review = await db.get(ReviewQueue, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    listing = await db.get(Listing, review.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Associated listing not found")

    listing.status = ListingStatus.REJECTED
    listing.rejection_reason = f"[{reject_data.template_code}] {reject_data.rejection_reason}"
    review.assigned_admin_id = admin_id
    review.reviewed_at = datetime.now(timezone.utc)
    review.reviewer_notes = reject_data.rejection_reason

    action_log = ReviewActionLog(
        review_queue_id=review.id,
        admin_id=admin_id,
        action="REJECT",
        reason=reject_data.rejection_reason,
        template_code=reject_data.template_code
    )
    db.add(action_log)

    audit_entry = SystemAuditLog(
        actor_id=admin_id,
        action_type="LISTING_REJECTED",
        resource_type="LISTING",
        resource_id=listing.id,
        details={
            "template_code": reject_data.template_code,
            "reason": reject_data.rejection_reason
        }
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(listing)
    return listing

async def request_additional_proof(review_id, admin_id, proof_data, db: AsyncSession):
    # Requests clearer shots from seller (e.g. blister seal or baseplate copyright)
    review = await db.get(ReviewQueue, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review item not found")

    listing = await db.get(Listing, review.listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Associated listing not found")

    listing.status = ListingStatus.ACTION_REQUIRED
    listing.rejection_reason = f"Additional proof required: {proof_data.reason}"
    review.assigned_admin_id = admin_id
    review.reviewed_at = datetime.now(timezone.utc)

    action_log = ReviewActionLog(
        review_queue_id=review.id,
        admin_id=admin_id,
        action="REQUEST_MORE_PROOF",
        reason=proof_data.reason,
        template_code="ACTION_REQUIRED"
    )
    db.add(action_log)

    await db.commit()
    await db.refresh(listing)
    return listing
