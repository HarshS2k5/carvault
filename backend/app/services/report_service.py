# Universal user report filing, priority triage, and anti-fraud penalty enforcement
import random
import string
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.report import UserReport, ReportTarget, ReportReason, ReportPriority, ReportStatus
from app.models.user import User, DeviceFingerprint, UserTrustScore
from app.models.listing import Listing, ListingStatus
from app.models.audit import SystemAuditLog

def generate_report_reference_id():
    # Human-readable reference ID e.g. "REP-2026-X892K"
    chars = string.ascii_uppercase + string.digits
    suffix = "".join(random.choice(chars) for _ in range(5))
    return f"REP-2026-{suffix}"

async def create_user_report(
    target_type: ReportTarget,
    target_id: str,
    reason: ReportReason,
    description: str,
    evidence_url: str = None,
    contact_email: str = None,
    reporter_id: str = None,
    db: AsyncSession = None
) -> UserReport:
    # Auto-classify priority: Counterfeits, fake photos, resealed cards, and off-platform payments are URGENT (<24h SLA)
    urgent_reasons = [
        ReportReason.FAKE_ITEM,
        ReportReason.FAKE_PHOTOS_VIDEO,
        ReportReason.RESEALED_PACKAGING,
        ReportReason.OFF_PLATFORM_PAYMENT,
        ReportReason.ILLEGAL_ITEM,
    ]
    priority = ReportPriority.URGENT if reason in urgent_reasons else ReportPriority.NORMAL

    ref_id = generate_report_reference_id()
    report = UserReport(
        reference_id=ref_id,
        reporter_id=reporter_id,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        description=description,
        evidence_url=evidence_url,
        contact_email=contact_email,
        priority=priority,
        status=ReportStatus.OPEN
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def enforce_report_action(
    report_id: str,
    admin_id: str,
    action: str, # 'REMOVE_LISTING', 'FREEZE_PAYOUT', 'PERMANENT_BAN', 'PENALIZE_FALSE_REPORT', 'DISMISS'
    admin_notes: str,
    db: AsyncSession
) -> UserReport:
    report = await db.get(UserReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.assigned_admin_id = admin_id
    report.resolution_action = action
    report.resolved_at = datetime.now(timezone.utc)

    # 1. Delist Listing
    if action == "REMOVE_LISTING":
        report.status = ReportStatus.ACTION_TAKEN
        if report.target_type == ReportTarget.LISTING:
            listing = await db.get(Listing, report.target_id)
            if listing:
                listing.status = ListingStatus.DELISTED
                listing.rejection_reason = f"Delisted by moderation report {report.reference_id}: {admin_notes}"

    # 2. Permanent Ban with Device & Bank Blacklisting
    elif action == "PERMANENT_BAN":
        report.status = ReportStatus.ACTION_TAKEN
        # Resolve target user
        user_to_ban = None
        if report.target_type == ReportTarget.PROFILE:
            user_to_ban = await db.get(User, report.target_id)
        elif report.target_type == ReportTarget.LISTING:
            listing = await db.get(Listing, report.target_id)
            if listing:
                listing.status = ListingStatus.DELISTED
                user_to_ban = await db.get(User, listing.seller_id)

        if user_to_ban:
            user_to_ban.is_banned = True
            user_to_ban.ban_reason = f"Fraud Enforcement via report {report.reference_id}: {admin_notes}"
            
            # Block all associated device fingerprints
            fp_stmt = select(DeviceFingerprint).where(DeviceFingerprint.user_id == user_to_ban.id)
            fp_res = await db.execute(fp_stmt)
            for fp in fp_res.scalars().all():
                fp.is_blocked = True

            # Freeze trust score and payout
            if user_to_ban.trust_score:
                user_to_ban.trust_score.score = 0
                user_to_ban.trust_score.active_listing_cap = 0
                user_to_ban.trust_score.risk_flags.append("PERMANENT_FRAUD_BAN")

    # 3. Penalize False Report
    elif action == "PENALIZE_FALSE_REPORT":
        report.status = ReportStatus.FALSE_REPORT_PENALIZED
        if report.reporter_id:
            reporter = await db.get(User, report.reporter_id)
            if reporter and reporter.trust_score:
                reporter.trust_score.score = max(0, reporter.trust_score.score - 20)
                reporter.trust_score.risk_flags.append("BAD_FAITH_REPORT_FILED")

    elif action == "DISMISS":
        report.status = ReportStatus.DISMISSED

    # Log to audit trail
    audit_entry = SystemAuditLog(
        actor_id=admin_id,
        action_type=f"REPORT_ACTION_{action}",
        resource_type="REPORT",
        resource_id=report.id,
        details={"reference_id": report.reference_id, "action": action, "notes": admin_notes}
    )
    db.add(audit_entry)

    await db.commit()
    await db.refresh(report)
    return report
