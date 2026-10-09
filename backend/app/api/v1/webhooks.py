# Gateway payment webhook endpoint with cryptographic HMAC signature verification
import json
from fastapi import APIRouter, Request, Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.payment_service import process_gateway_webhook

router = APIRouter()

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    # Receives signed payment events from Razorpay Route
    # Verifies HMAC signature, prevents replay attacks, and safely transitions escrow state
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header"
        )

    # Read raw body bytes for exact HMAC validation
    raw_body = await request.body()
    try:
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload in webhook body"
        )

    event_id = payload.get("event_id") or payload.get("id") or f"evt_mock_{hash(raw_body)}"
    event_type = payload.get("event", "payment.captured")

    result = await process_gateway_webhook(
        event_id=event_id,
        event_type=event_type,
        signature=x_razorpay_signature,
        payload=payload,
        raw_body=raw_body,
        db=db
    )
    return result
