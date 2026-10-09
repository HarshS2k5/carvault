# Universal user report filing and administrative enforcement API router
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.models.report import UserReport, ReportTarget, ReportReason, ReportPriority, ReportStatus
from app.services.report_service import create_user_report, enforce_report_action

router = APIRouter()

class CreateReportRequest(BaseModel):
    target_type: ReportTarget
    target_id: str
    reason: ReportReason
    description: str = Field(..., min_length=10)
    evidence_url: Optional[str] = None
    contact_email: Optional[str] = None

class EnforceActionRequest(BaseModel):
    action: str = Field(..., description="'REMOVE_LISTING', 'FREEZE_PAYOUT', 'PERMANENT_BAN', 'PENALIZE_FALSE_REPORT', 'DISMISS'")
    admin_notes: str = Field(..., min_length=5)

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_report(
    payload: CreateReportRequest,
    db: AsyncSession = Depends(get_db)
):
    # Universal Report Button handler: files report and returns tracking reference ID
    report = await create_user_report(
        target_type=payload.target_type,
        target_id=payload.target_id,
        reason=payload.reason,
        description=payload.description,
        evidence_url=payload.evidence_url,
        contact_email=payload.contact_email,
        db=db
    )
    return {
        "reference_id": report.reference_id,
        "priority": report.priority.value,
        "status": report.status.value,
        "message": f"Report lodged with reference {report.reference_id}. Our Trust & Safety team will review within our SLA target."
    }

@router.get("/admin/queue")
async def list_reports_queue(
    priority: Optional[ReportPriority] = None,
    limit: int = Query(50, le=100),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Prioritized queue: fraud and illegal items sorted first
    stmt = select(UserReport).order_by(
        UserReport.priority.desc(),
        UserReport.created_at.desc()
    ).limit(limit)

    if priority:
        stmt = stmt.where(UserReport.priority == priority)

    res = await db.execute(stmt)
    reports = res.scalars().all()
    return reports

@router.post("/admin/{report_id}/enforce")
async def take_report_action(
    report_id: str,
    payload: EnforceActionRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Enforces moderation penalties (e.g. banning user, blacklisting device and bank account)
    report = await enforce_report_action(
        report_id=report_id,
        admin_id=current_admin.id,
        action=payload.action,
        admin_notes=payload.admin_notes,
        db=db
    )
    return {
        "reference_id": report.reference_id,
        "status": report.status.value,
        "action_taken": report.resolution_action,
        "message": f"Action {payload.action} successfully enforced on target."
    }
