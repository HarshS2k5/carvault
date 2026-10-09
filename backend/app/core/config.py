# Configuration settings for CarVault backend
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # Application identity
    PROJECT_NAME: str = "CarVault"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "carvault-dev-secret-key-replace-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days for mobile app session

    # Database connection: defaults to local sqlite async for zero-friction setup, PostgreSQL in prod
    DATABASE_URL: str = "sqlite+aiosqlite:///./carvault.db"

    # Escrow & Commission Configuration (amounts in basis points or integer paise)
    COMMISSION_RATE_BETA_BPS: int = 300  # 3.0% commission in beta
    COMMISSION_RATE_LAUNCH_BPS: int = 700  # 7.0% commission at full launch
    MIN_ORDER_COMMISSION_PAISE: int = 2500  # Minimum platform fee of ₹25 (2500 paise)
    INSPECTION_WINDOW_HOURS: int = 48  # 48-hour buyer inspection window before payout auto-release

    # Storage for listing photos, verification proofs, packing/unboxing videos
    STORAGE_BUCKET_NAME: str = "carvault-media"
    STORAGE_PUBLIC_BASE_URL: str = "https://media.carvault.in"

    # Gateway sandbox keys (Razorpay Route / Cashfree Easy Split)
    GATEWAY_KEY_ID: Optional[str] = "rzp_test_placeholder"
    GATEWAY_KEY_SECRET: Optional[str] = "rzp_secret_placeholder"
    GATEWAY_WEBHOOK_SECRET: str = "carvault_whsec_dev"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="allow")

settings = Settings()
