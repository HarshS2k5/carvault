# Trust score calculation, anomaly detection, and risk flagging engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User, UserTrustScore, KycTier, DeviceFingerprint
from app.models.listing import Listing, ListingStatus, DiecastCatalog

async def calculate_and_update_trust_score(user_id: str, db: AsyncSession) -> UserTrustScore:
    # Computes dynamic trust score (0 - 100) based on KYC tier, order history, disputes, and reports
    user = await db.get(User, user_id)
    if not user:
        return None

    trust = user.trust_score
    if not trust:
        trust = UserTrustScore(user_id=user.id, score=50)
        db.add(trust)
        await db.flush()

    # Base score
    base = 50

    # KYC Tier weight
    if user.kyc_tier == KycTier.TIER_1_VERIFIED:
        base += 25
    elif user.kyc_tier == KycTier.TIER_2_PRO:
        base += 40

    # Completed orders bonus (+2 per completed order, max +30)
    base += min(30, trust.completed_orders * 2)

    # Disputes and refunds penalties
    base -= (trust.dispute_count * 15)
    base -= (trust.refund_count * 20)

    # Reports penalty
    base -= (trust.report_count * 10)

    # Bound within 0 to 100
    final_score = max(0, min(100, base))
    trust.score = final_score

    # Dynamically set listing cap and payout hold based on trust tier
    if user.is_banned or final_score < 30:
        trust.active_listing_cap = 0
        trust.payout_hold_hours = 72
    elif user.kyc_tier == KycTier.TIER_0_NEW or final_score < 60:
        trust.active_listing_cap = 3
        trust.payout_hold_hours = 48
    elif user.kyc_tier == KycTier.TIER_1_VERIFIED:
        trust.active_listing_cap = 25
        trust.payout_hold_hours = 24
    else: # Pro tier
        trust.active_listing_cap = 100
        trust.payout_hold_hours = 12

    await db.commit()
    await db.refresh(trust)
    return trust

async def detect_account_anomalies(user_id: str, db: AsyncSession) -> list:
    # Detects high-risk patterns: shared device sybil accounts, new account rare item spam
    flags = []
    user = await db.get(User, user_id)
    if not user:
        return flags

    # 1. Shared Device Multi-Account Check: check if user's device is linked to other phone numbers
    fp_stmt = select(DeviceFingerprint).where(DeviceFingerprint.user_id == user_id)
    fp_res = await db.execute(fp_stmt)
    my_fingerprints = fp_res.scalars().all()

    for fp in my_fingerprints:
        shared_stmt = select(DeviceFingerprint).where(
            DeviceFingerprint.device_hash == fp.device_hash,
            DeviceFingerprint.user_id != user_id
        )
        shared_res = await db.execute(shared_stmt)
        if shared_res.scalars().first():
            flags.append("SHARED_DEVICE_MULTI_ACCOUNT")
            break

    # 2. New Account Rare Item Flag: Tier 0 account listing >= 3 high-value STH / Car Culture items
    if user.kyc_tier == KycTier.TIER_0_NEW:
        rare_stmt = select(func.count(Listing.id)).where(
            Listing.seller_id == user_id,
            Listing.price_paise >= 200000 # >= ₹2,000 items
        )
        rare_res = await db.execute(rare_stmt)
        rare_count = rare_res.scalar_one()
        if rare_count >= 3:
            flags.append("NEW_ACCOUNT_RARE_ITEMS_SPIKE")

    # Update risk flags on trust score record
    if user.trust_score:
        existing_flags = set(user.trust_score.risk_flags or [])
        existing_flags.update(flags)
        user.trust_score.risk_flags = list(existing_flags)
        await db.commit()

    return flags
