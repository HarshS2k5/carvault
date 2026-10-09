# Pydantic schemas for Authentication and KYC workflows
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole, KycTier, KycStatus

class OtpSendRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+91[6-9]\d{9}$", description="Indian mobile number with +91 prefix")

class OtpSendResponse(BaseModel):
    message: str
    phone_number: str
    expires_in_seconds: int = 300

class OtpVerifyRequest(BaseModel):
    phone_number: str = Field(..., pattern=r"^\+91[6-9]\d{9}$")
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit mobile OTP code")
    device_hash: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: UserRole
    kyc_tier: KycTier

class UserProfileResponse(BaseModel):
    id: str
    phone_number: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: UserRole
    kyc_tier: KycTier
    is_active: bool
    is_banned: bool
    trust_score: Optional[int] = 50

    model_config = ConfigDict(from_attributes=True)

class KycInitiateRequest(BaseModel):
    # DigiLocker flow initiation
    pan_number: str = Field(..., pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", description="Valid Indian PAN card number")
    full_name_as_per_pan: str

class PennyDropRequest(BaseModel):
    account_number: str = Field(..., min_length=9, max_length=18)
    ifsc_code: str = Field(..., min_length=11, max_length=11)

class PennyDropResponse(BaseModel):
    is_successful: bool
    beneficiary_name: str
    name_match_score: float
    message: str
