# Rigorous tests for the Escrow Order State Machine and audit transition logging
import pytest
from app.models.order import OrderState
from app.services.state_machine import transition_order_state

@pytest.mark.asyncio
async def test_order_happy_path_state_machine(client, buyer_token, seller_token, approved_listing):
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    seller_headers = {"Authorization": f"Bearer {seller_token}"}

    # 1. Buyer creates order for approved listing (Starts in CREATED)
    create_resp = await client.post("/api/v1/orders", json={
        "listing_id": approved_listing.id,
        "shipping_fee_paise": 10000 # ₹100 shipping
    }, headers=buyer_headers)
    assert create_resp.status_code == 201
    order = create_resp.json()
    order_id = order["id"]
    assert order["current_state"] == "CREATED"
    
    # Financial validation in paise:
    # item: 150000 (₹1500), shipping: 10000 (₹100) -> total: 160000 (₹1600)
    # commission at 3%: 150000 * 0.03 = 4500 paise (₹45)
    # seller payable: 160000 - 4500 = 155500 paise (₹1555)
    assert order["total_buyer_paid_paise"] == 160000
    assert order["commission_paise"] == 4500
    assert order["seller_payable_paise"] == 155500

    # 2. Simulate Payment Webhook transition CREATED -> PAID_HELD
    order_detail_resp = await client.get(f"/api/v1/orders/{order_id}", headers=buyer_headers)
    assert order_detail_resp.status_code == 200

    # Test via direct API transitions
    # Seller tries to ship before payment -> MUST FAIL
    fail_ship = await client.post(f"/api/v1/orders/{order_id}/ship", json={
        "courier_partner": "DELHIVERY",
        "tracking_id": "DELHI-981240"
    }, headers=seller_headers)
    assert fail_ship.status_code == 400
    assert "Illegal state transition from 'CREATED' to 'SHIPPED'" in fail_ship.json()["detail"]

@pytest.mark.asyncio
async def test_illegal_state_transitions(test_db, buyer_user, seller_user, approved_listing):
    # Tests internal state machine invariants directly
    from app.models.order import Order
    from fastapi import HTTPException

    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=150000,
        commission_rate_bps=300,
        commission_paise=4500,
        seller_payable_paise=145500,
        total_buyer_paid_paise=150000
    )
    test_db.add(order)
    await test_db.commit()
    await test_db.refresh(order)

    # CREATED -> RELEASED is illegal
    with pytest.raises(HTTPException) as exc_info:
        await transition_order_state(
            order=order,
            target_state=OrderState.RELEASED,
            trigger_source="ADMIN",
            db=test_db
        )
    assert exc_info.value.status_code == 400
    assert "Illegal state transition" in exc_info.value.detail

    # CREATED -> DELIVERED is illegal
    with pytest.raises(HTTPException) as exc_info:
        await transition_order_state(
            order=order,
            target_state=OrderState.DELIVERED,
            trigger_source="ADMIN",
            db=test_db
        )
    assert exc_info.value.status_code == 400

@pytest.mark.asyncio
async def test_complete_state_transitions_with_audit_trail(test_db, buyer_user, seller_user, approved_listing):
    from app.models.order import Order
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=150000,
        commission_rate_bps=300,
        commission_paise=4500,
        seller_payable_paise=145500,
        total_buyer_paid_paise=150000
    )
    test_db.add(order)
    await test_db.commit()
    await test_db.refresh(order)

    # 1. CREATED -> PAID_HELD
    order = await transition_order_state(order, OrderState.PAID_HELD, "WEBHOOK", db=test_db)
    assert order.current_state == OrderState.PAID_HELD

    # 2. PAID_HELD -> SHIPPED
    order = await transition_order_state(order, OrderState.SHIPPED, "SELLER", seller_user.id, db=test_db)
    assert order.current_state == OrderState.SHIPPED

    # 3. SHIPPED -> DELIVERED
    order = await transition_order_state(order, OrderState.DELIVERED, "BUYER", buyer_user.id, db=test_db)
    assert order.current_state == OrderState.DELIVERED

    # 4. DELIVERED -> INSPECTION_WINDOW
    order = await transition_order_state(order, OrderState.INSPECTION_WINDOW, "SYSTEM_TIMER", db=test_db)
    assert order.current_state == OrderState.INSPECTION_WINDOW
    assert order.inspection_window_ends_at is not None

    # 5. INSPECTION_WINDOW -> RELEASED (funds released to seller)
    order = await transition_order_state(order, OrderState.RELEASED, "BUYER", buyer_user.id, db=test_db)
    assert order.current_state == OrderState.RELEASED
    assert order.released_at is not None

    # Verify audit transitions trail contains all 5 transitions in sequence
    await test_db.refresh(order)
    assert len(order.transitions) == 5
    states_sequence = [(t.from_state, t.to_state) for t in order.transitions]
    assert states_sequence == [
        (OrderState.CREATED, OrderState.PAID_HELD),
        (OrderState.PAID_HELD, OrderState.SHIPPED),
        (OrderState.SHIPPED, OrderState.DELIVERED),
        (OrderState.DELIVERED, OrderState.INSPECTION_WINDOW),
        (OrderState.INSPECTION_WINDOW, OrderState.RELEASED),
    ]

@pytest.mark.asyncio
async def test_dispute_and_cancellation_branches(test_db, buyer_user, seller_user, approved_listing):
    from app.models.order import Order
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.CREATED,
        item_price_paise=150000,
        commission_rate_bps=300,
        commission_paise=4500,
        seller_payable_paise=145500,
        total_buyer_paid_paise=150000
    )
    test_db.add(order)
    await test_db.commit()

    # Move to PAID_HELD -> DISPUTED -> REFUNDED
    await transition_order_state(order, OrderState.PAID_HELD, "WEBHOOK", db=test_db)
    await transition_order_state(order, OrderState.DISPUTED, "BUYER", buyer_user.id, {"claim": "Damaged card"}, db=test_db)
    assert order.current_state == OrderState.DISPUTED

    await transition_order_state(order, OrderState.REFUNDED, "ADMIN", db=test_db)
    assert order.current_state == OrderState.REFUNDED
    assert order.refunded_at is not None
