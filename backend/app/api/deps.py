# API route dependencies for authentication, DB session, and role-based access control
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

# Standard bearer token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/otp/verify", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    # Validates JWT token from Authorization header and fetches active user
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required"
        )
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User account not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is deactivated")
    if user.is_banned:
        raise HTTPException(status_code=403, detail=f"Account banned: {user.ban_reason}")
    return user

async def get_current_admin(current_user: User = Depends(get_current_user)):
    # Restricts endpoint to platform administrators and certified reviewers
    if current_user.role not in [UserRole.ADMIN, UserRole.REVIEWER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to authorized reviewers and administrators"
        )
    return current_user
