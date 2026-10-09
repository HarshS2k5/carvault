# Dispute resolution endpoints with evidence comparison
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.dispute import Dispute, DisputeStatus, DisputeEvidence
from app.services.dispute_service import open_order_dispute, attach_seller_packing_evidence, resolve_dispute_by_admin

router = APIRouter()

class CreateDisputeRequest(BaseModel):
    order_id: str
    reason: str = Field(..., min_length=10)
    unboxing_video_url: Optional[str] = None

class SellerEvidenceRequest(BaseModel):
    packing_video_url: str = Field(..., min_length=5)

class ResolveDisputeRequest(BaseModel):
    action: str = Field(..., description="'RELEASE_TO_SELLER' or 'REFUND_TO_BUYER'")
    admin_notes: str = Field(..., min_length=5)

@router.post("", status_code=status.HTTP_201_CREATED)
async def file_dispute(
    payload: CreateDisputeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Freezes payout and opens inspection claim with continuous unboxing video
    dispute = await open_order_dispute(
        order_id=payload.order_id,
        buyer_id=current_user.id,
        reason=payload.reason,
        unboxing_video_url=payload.unboxing_video_url,
        db=db
    )
    return {
        "dispute_id": dispute.id,
        "order_id": dispute.order_id,
        "status": dispute.status.value,
        "message": "Dispute opened successfully. Payout is frozen pending review."
    }

@router.post("/{dispute_id}/seller-evidence")
async def upload_seller_evidence(
    dispute_id: str,
    payload: SellerEvidenceRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Seller uploads packing video to counter the buyer's claim
    evidence = await attach_seller_packing_evidence(
        dispute_id=dispute_id,
        seller_id=current_user.id,
        packing_video_url=payload.packing_video_url,
        db=db
    )
    return {
        "evidence_id": evidence.id,
        "status": "UNDER_REVIEW",
        "message": "Seller packing proof submitted to moderation queue."
    }

@router.get("/admin/queue")
async def list_dispute_queue(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Fetches active disputes requiring human arbitration
    stmt = (
        select(Dispute)
        .options(
            selectinload(Dispute.evidence),
            selectinload(Dispute.order)
        )
        .order_by(Dispute.created_at.desc())
    )
    res = await db.execute(stmt)
    disputes = res.scalars().all()
    return disputes

@router.get("/admin/{dispute_id}/compare")
async def compare_evidence_side_by_side(
    dispute_id: str,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Retrieves both seller packing video and buyer unboxing video side-by-side
    dispute = await db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    seller_evidence = next((e for e in dispute.evidence if e.uploader_role == "SELLER"), None)
    buyer_evidence = next((e for e in dispute.evidence if e.uploader_role == "BUYER"), None)

    return {
        "dispute_id": dispute.id,
        "order_id": dispute.order_id,
        "status": dispute.status.value,
        "reason": dispute.reason,
        "seller_packing_video": seller_evidence.file_url if seller_evidence else None,
        "buyer_unboxing_video": buyer_evidence.file_url if buyer_evidence else None,
        "created_at": dispute.created_at
    }

@router.post("/admin/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    payload: ResolveDisputeRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Final resolution: either releases held escrow to seller or refunds buyer
    dispute = await resolve_dispute_by_admin(
        dispute_id=dispute_id,
        admin_id=current_admin.id,
        action=payload.action,
        admin_notes=payload.admin_notes,
        db=db
    )
    return {
        "dispute_id": dispute.id,
        "status": dispute.status.value,
        "resolution": dispute.resolution_action,
        "message": "Dispute resolved and escrow executed."
    }
