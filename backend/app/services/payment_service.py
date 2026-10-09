# Payment gateway integration, split calculation, HMAC verification, and idempotent webhook processing
import hmac
import hashlib
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.core.config import settings
from app.models.order import Order, OrderState
from app.models.payment import PaymentTransaction, GatewayWebhookLog
from app.services.state_machine import transition_order_state

def calculate_order_financials(item_price_paise: int, shipping_fee_paise: int = 0) -> dict:
    # Computes commission in integer paise based on beta tier (300 bps / 3.0%) with minimum floor
    commission_rate_bps = settings.COMMISSION_RATE_BETA_BPS
    calculated_commission = int((item_price_paise * commission_rate_bps) / 10000)
    
    # Enforce minimum platform fee of ₹25 (2500 paise)
    final_commission = max(calculated_commission, settings.MIN_ORDER_COMMISSION_PAISE)
    
    total_buyer_paid = item_price_paise + shipping_fee_paise
    seller_payable = total_buyer_paid - final_commission

    return {
        "item_price_paise": item_price_paise,
        "shipping_fee_paise": shipping_fee_paise,
        "commission_rate_bps": commission_rate_bps,
        "commission_paise": final_commission,
        "min_platform_fee_paise": settings.MIN_ORDER_COMMISSION_PAISE,
        "seller_payable_paise": seller_payable,
        "total_buyer_paid_paise": total_buyer_paid,
    }

def verify_webhook_hmac_signature(raw_body: bytes, received_signature: str) -> bool:
    # Verifies HMAC-SHA256 signature sent in webhook headers against webhook secret
    if not received_signature or not settings.GATEWAY_WEBHOOK_SECRET:
        return False
    expected_signature = hmac.new(
        key=settings.GATEWAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, received_signature)

async def process_gateway_webhook(
    event_id: str,
    event_type: str,
    signature: str,
    payload: dict,
    raw_body: bytes,
    db: AsyncSession
) -> dict:
    # Strictly idempotent webhook processor that verifies signature and updates escrow state
    # 1. Signature Verification: Never trust raw incoming webhooks
    is_valid = verify_webhook_hmac_signature(raw_body, signature)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid gateway webhook HMAC signature"
        )

    # 2. Idempotency Check: prevent double-crediting or duplicate transitions on gateway retries
    stmt = select(GatewayWebhookLog).where(GatewayWebhookLog.event_id == event_id)
    res = await db.execute(stmt)
    existing_log = res.scalars().first()

    if existing_log and existing_log.is_processed:
        return {
            "status": "already_processed",
            "event_id": event_id,
            "message": "Webhook already executed; acknowledged idempotently"
        }

    # Record or update webhook log entry
    if not existing_log:
        webhook_log = GatewayWebhookLog(
            event_id=event_id,
            event_type=event_type,
            signature=signature,
            is_verified=True,
            is_processed=False
        )
        db.add(webhook_log)
        await db.flush()
    else:
        webhook_log = existing_log

    # 3. Handle Supported Event Types
    if event_type in ["payment.captured", "order.paid"]:
        payment_data = payload.get("payload", {}).get("payment", {}).get("entity", {}) or payload.get("payment", {})
        gateway_order_id = payment_data.get("order_id")
        gateway_payment_id = payment_data.get("id") or f"pay_{event_id[:16]}"
        amount_paise = payment_data.get("amount", 0)

        # Look up corresponding CarVault Order
        order_stmt = select(Order).where(Order.gateway_order_id == gateway_order_id)
        order_res = await db.execute(order_stmt)
        order = order_res.scalars().first()

        if order:
            order.gateway_payment_id = gateway_payment_id

            # Record payment transaction record
            tx = PaymentTransaction(
                order_id=order.id,
                gateway_name="RAZORPAY_ROUTE",
                gateway_payment_id=gateway_payment_id,
                amount_paise=amount_paise or order.total_buyer_paid_paise,
                currency="INR",
                status="CAPTURED",
                raw_payload=payload
            )
            db.add(tx)

            # Move state machine from CREATED -> PAID_HELD
            if order.current_state == OrderState.CREATED:
                await transition_order_state(
                    order=order,
                    target_state=OrderState.PAID_HELD,
                    trigger_source="WEBHOOK",
                    metadata={"gateway_payment_id": gateway_payment_id, "amount_paise": amount_paise},
                    db=db
                )
                # Record double-entry ledger transaction: Debit Escrow Nodal, Credit Buyer Funds Held
                from app.services.ledger_service import record_payment_captured_ledger
                await record_payment_captured_ledger(order, gateway_payment_id, db)

    # Mark webhook log as processed
    webhook_log.is_processed = True
    webhook_log.processed_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "status": "success",
        "event_id": event_id,
        "event_type": event_type
    }
