# Tests for HMAC signature verification and idempotent webhook execution
import json
import hmac
import hashlib
import pytest
from app.core.config import settings
from app.models.order import Order, OrderState

def generate_hmac_signature(body: bytes, secret: str) -> str:
    # Computes valid HMAC-SHA256 signature for test payload
    return hmac.new(key=secret.encode("utf-8"), msg=body, digestmod=hashlib.sha256).hexdigest()

@pytest.mark.asyncio
async def test_signed_webhook_transitions_order_and_is_idempotent(client, test_db, buyer_user, seller_user, approved_listing):
    # 1. Setup order in CREATED state
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=150000,
        commission_rate_bps=300,
        commission_paise=4500,
        seller_payable_paise=145500,
        total_buyer_paid_paise=150000,
        gateway_order_id="order_rzp_mock_12345"
    )
    test_db.add(order)
    await test_db.commit()
    await test_db.refresh(order)

    # 2. Build webhook payload for payment.captured
    event_id = "evt_rzp_payment_captured_99"
    webhook_dict = {
        "event_id": event_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_mock_777888",
                    "order_id": "order_rzp_mock_12345",
                    "amount": 150000,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }
    raw_body = json.dumps(webhook_dict).encode("utf-8")
    valid_sig = generate_hmac_signature(raw_body, settings.GATEWAY_WEBHOOK_SECRET)

    # 3. Post webhook with INVALID signature -> must fail with 401
    bad_resp = await client.post(
        "/api/v1/payments/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": "invalid_tampered_signature"}
    )
    assert bad_resp.status_code == 401

    # 4. Post webhook with VALID signature -> successfully transitions order to PAID_HELD
    good_resp = await client.post(
        "/api/v1/payments/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": valid_sig}
    )
    assert good_resp.status_code == 200
    res_json = good_resp.json()
    assert res_json["status"] == "success"

    # Verify order state updated to PAID_HELD
    await test_db.refresh(order)
    assert order.current_state == OrderState.PAID_HELD
    assert order.gateway_payment_id == "pay_mock_777888"

    # 5. IDEMPOTENCY TEST: Post EXACT SAME webhook a second time
    replay_resp = await client.post(
        "/api/v1/payments/webhooks/razorpay",
        content=raw_body,
        headers={"X-Razorpay-Signature": valid_sig}
    )
    assert replay_resp.status_code == 200
    replay_json = replay_resp.json()
    assert replay_json["status"] == "already_processed"
    assert "acknowledged idempotently" in replay_json["message"]

    # Verify order state remained PAID_HELD without duplicate transitions
    await test_db.refresh(order)
    assert order.current_state == OrderState.PAID_HELD
    assert len(order.transitions) == 1
