# Dispute resolution service with side-by-side evidence collation
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.order import Order, OrderState
from app.models.dispute import Dispute, DisputeStatus, DisputeEvidence
from app.models.audit import SystemAuditLog
from app.services.state_machine import transition_order_state

async def open_order_dispute(
    order_id: str,
    buyer_id: str,
    reason: str,
    unboxing_video_url: str = None,
    db: AsyncSession = None
) -> Dispute:
    # Freezes payout and initializes a dispute case
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_id != buyer_id:
        raise HTTPException(status_code=403, detail="Only buyer can dispute this order")

    # Transition order state to DISPUTED
    await transition_order_state(
        order=order,
        target_state=OrderState.DISPUTED,
        trigger_source="BUYER",
        triggered_by_id=buyer_id,
        metadata={"reason": reason},
        db=db
    )

    # Create dispute case
    dispute = Dispute(
        order_id=order.id,
        raised_by_id=buyer_id,
        reason=reason,
        status=DisputeStatus.OPENED
    )
    db.add(dispute)
    await db.flush()

    # Attach buyer unboxing video evidence if provided
    if unboxing_video_url:
        evidence = DisputeEvidence(
            dispute_id=dispute.id,
            uploader_id=buyer_id,
            uploader_role="BUYER",
            file_url=unboxing_video_url,
            file_type="VIDEO",
            description="Buyer continuous unboxing video showing card and car condition upon parcel opening"
        )
        db.add(evidence)

    await db.commit()
    await db.refresh(dispute)
    return dispute

async def attach_seller_packing_evidence(
    dispute_id: str,
    seller_id: str,
    packing_video_url: str,
    db: AsyncSession
) -> DisputeEvidence:
    # Seller uploads video showing pre-dispatch packaging condition
    dispute = await db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    evidence = DisputeEvidence(
        dispute_id=dispute.id,
        uploader_id=seller_id,
        uploader_role="SELLER",
        file_url=packing_video_url,
        file_type="VIDEO",
        description="Seller pre-dispatch packing video showing card condition and bubble wrap sealing"
    )
    db.add(evidence)
    dispute.status = DisputeStatus.UNDER_REVIEW
    await db.commit()
    await db.refresh(evidence)
    return evidence

async def resolve_dispute_by_admin(
    dispute_id: str,
    admin_id: str,
    action: str, # 'RELEASE_TO_SELLER' or 'REFUND_TO_BUYER'
    admin_notes: str,
    db: AsyncSession
) -> Dispute:
    # Admin inspects evidence side-by-side and issues final resolution
    dispute = await db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")

    order = await db.get(Order, dispute.order_id)
    dispute.resolved_by_id = admin_id
    dispute.admin_notes = admin_notes
    dispute.resolved_at = datetime.now(timezone.utc)
    dispute.resolution_action = action

    if action == "RELEASE_TO_SELLER":
        dispute.status = DisputeStatus.RESOLVED_RELEASED
        await transition_order_state(
            order=order,
            target_state=OrderState.RELEASED,
            trigger_source="ADMIN",
            triggered_by_id=admin_id,
            metadata={"notes": admin_notes, "dispute_id": dispute.id},
            db=db
        )
    elif action == "REFUND_TO_BUYER":
        dispute.status = DisputeStatus.RESOLVED_REFUNDED
        await transition_order_state(
            order=order,
            target_state=OrderState.REFUNDED,
            trigger_source="ADMIN",
            triggered_by_id=admin_id,
            metadata={"notes": admin_notes, "dispute_id": dispute.id},
            db=db
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid dispute resolution action")

    await db.commit()
    await db.refresh(dispute)
    return dispute
