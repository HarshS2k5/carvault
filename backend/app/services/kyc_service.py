# KYC verification service complying with Indian financial regulations
# Strictly NEVER stores 12-digit Aadhaar numbers. Stores verification reference IDs and masked PAN.
from datetime import datetime, timezone
from difflib import SequenceMatcher
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.user import User, KycVerification, KycTier, KycStatus
from app.models.audit import SystemAuditLog

def calculate_name_similarity(name1, name2):
    # Computes normalized string match percentage between user-provided name and bank record
    if not name1 or not name2:
        return 0.0
    n1 = name1.strip().upper()
    n2 = name2.strip().upper()
    return round(SequenceMatcher(None, n1, n2).ratio() * 100.0, 2)

async def initiate_or_update_pan_kyc(user_id, pan_number, full_name, db: AsyncSession):
    # Mask PAN: show first 5 and last 1 characters (e.g. ABCDE****F)
    masked_pan = f"{pan_number[:5]}****{pan_number[-1]}"
    
    # Retrieve user
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve or create KYC record
    stmt = select(KycVerification).where(KycVerification.user_id == user_id)
    result = await db.execute(stmt)
    kyc = result.scalars().first()

    if not kyc:
        kyc = KycVerification(
            user_id=user_id,
            pan_number_masked=masked_pan,
            digilocker_request_id=f"DGL-{user_id[:8]}",
            status=KycStatus.PENDING
        )
        db.add(kyc)
    else:
        kyc.pan_number_masked = masked_pan

    user.full_name = full_name
    await db.commit()
    await db.refresh(kyc)
    return kyc

async def process_penny_drop_verification(user_id, account_number, ifsc_code, db: AsyncSession):
    # Simulates RBI-compliant penny drop verification (depositing ₹1.00 into seller account)
    # Verifies account activity and matches legal beneficiary name
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = select(KycVerification).where(KycVerification.user_id == user_id)
    result = await db.execute(stmt)
    kyc = result.scalars().first()

    if not kyc:
        kyc = KycVerification(user_id=user_id, status=KycStatus.PENDING)
        db.add(kyc)

    # Simulated bank response for test environment
    simulated_bank_name = user.full_name or "COLLECTOR DEMO NAME"
    similarity = calculate_name_similarity(user.full_name, simulated_bank_name)

    # Mask bank account number (keep last 4 digits)
    masked_acc = f"{'*' * (len(account_number) - 4)}{account_number[-4:]}"

    kyc.bank_account_masked = masked_acc
    kyc.bank_ifsc = ifsc_code.upper()
    kyc.bank_penny_drop_name = simulated_bank_name
    kyc.penny_drop_name_match_score = similarity

    # If name match is above 80%, approve Tier 1 Verified status
    if similarity >= 80.0:
        kyc.status = KycStatus.APPROVED
        kyc.verified_at = datetime.now(timezone.utc)
        user.kyc_tier = KycTier.TIER_1_VERIFIED
        
        # Increase listing cap for verified seller
        if user.trust_score:
            user.trust_score.active_listing_cap = 25
            user.trust_score.score = max(user.trust_score.score, 75)

        # Log to audit table for compliance
        audit_entry = SystemAuditLog(
            actor_id=user_id,
            action_type="KYC_VERIFIED_TIER_1",
            resource_type="USER",
            resource_id=user_id,
            details={
                "bank_match_score": similarity,
                "masked_account": masked_acc,
                "ifsc": ifsc_code.upper()
            }
        )
        db.add(audit_entry)
    else:
        kyc.status = KycStatus.REJECTED
        kyc.rejection_reason = f"Bank account name mismatch ({similarity}% match)"

    await db.commit()
    return {
        "is_successful": similarity >= 80.0,
        "beneficiary_name": simulated_bank_name,
        "name_match_score": similarity,
        "message": "Penny drop verified successfully" if similarity >= 80.0 else "Name mismatch on bank account"
    }
