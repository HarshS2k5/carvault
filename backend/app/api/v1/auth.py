# Auth and KYC endpoints
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import (
    OtpSendRequest, OtpSendResponse,
    OtpVerifyRequest, TokenResponse,
    UserProfileResponse, KycInitiateRequest,
    PennyDropRequest, PennyDropResponse
)
from app.services.auth_service import generate_otp, verify_otp_and_authenticate
from app.services.kyc_service import initiate_or_update_pan_kyc, process_penny_drop_verification
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

@router.post("/otp/send", response_model=OtpSendResponse)
async def send_otp(payload: OtpSendRequest):
    # Generates a one-time password for Indian phone numbers
    code = generate_otp(payload.phone_number)
    return OtpSendResponse(
        message=f"OTP dispatched successfully (Dev code: {code})",
        phone_number=payload.phone_number
    )

@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(payload: OtpVerifyRequest, db: AsyncSession = Depends(get_db)):
    # Validates mobile OTP and yields JWT session token
    auth_data = await verify_otp_and_authenticate(
        phone_number=payload.phone_number,
        otp_code=payload.otp_code,
        device_hash=payload.device_hash,
        db=db
    )
    return auth_data

@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    # Retrieves the authenticated user's profile and trust metrics
    score = current_user.trust_score.score if current_user.trust_score else 50
    return UserProfileResponse(
        id=current_user.id,
        phone_number=current_user.phone_number,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        kyc_tier=current_user.kyc_tier,
        is_active=current_user.is_active,
        is_banned=current_user.is_banned,
        trust_score=score
    )

@router.post("/kyc/pan")
async def submit_pan_kyc(
    payload: KycInitiateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # DigiLocker PAN submission; stores masked PAN only
    kyc_record = await initiate_or_update_pan_kyc(
        user_id=current_user.id,
        pan_number=payload.pan_number,
        full_name=payload.full_name_as_per_pan,
        db=db
    )
    return {
        "status": kyc_record.status,
        "masked_pan": kyc_record.pan_number_masked,
        "message": "PAN verified. Please proceed with bank penny-drop verification."
    }

@router.post("/kyc/penny-drop", response_model=PennyDropResponse)
async def submit_penny_drop(
    payload: PennyDropRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verifies beneficiary name and bank account for seller payouts
    result = await process_penny_drop_verification(
        user_id=current_user.id,
        account_number=payload.account_number,
        ifsc_code=payload.ifsc_code,
        db=db
    )
    return result
