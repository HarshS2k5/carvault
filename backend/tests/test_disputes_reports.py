# Tests for disputes, side-by-side evidence arbitration, universal report filing, and anti-fraud ban enforcement
import pytest
from app.models.order import Order, OrderState
from app.models.user import DeviceFingerprint
from app.models.report import ReportPriority

@pytest.mark.asyncio
async def test_dispute_lifecycle_and_admin_arbitration(client, test_db, buyer_token, seller_token, admin_token, buyer_user, seller_user, approved_listing):
    buyer_headers = {"Authorization": f"Bearer {buyer_token}"}
    seller_headers = {"Authorization": f"Bearer {seller_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Setup order in PAID_HELD
    order = Order(
        listing_id=approved_listing.id,
        buyer_id=buyer_user.id,
        seller_id=seller_user.id,
        current_state=OrderState.PAID_HELD,
        item_price_paise=150000,
        commission_rate_bps=300,
        commission_paise=4500,
        seller_payable_paise=145500,
        total_buyer_paid_paise=150000
    )
    test_db.add(order)
    await test_db.commit()
    await test_db.refresh(order)

    # 2. Buyer opens dispute with unboxing video
    dispute_resp = await client.post("/api/v1/disputes", json={
        "order_id": order.id,
        "reason": "Damaged blister card upon unboxing, soft corners not disclosed.",
        "unboxing_video_url": "https://media.carvault.in/buyer_unboxing_proof.mp4"
    }, headers=buyer_headers)
    assert dispute_resp.status_code == 201
    dispute_id = dispute_resp.json()["dispute_id"]

    # Verify order state is now frozen in DISPUTED
    await test_db.refresh(order)
    assert order.current_state == OrderState.DISPUTED

    # 3. Seller attaches counter evidence: packing video
    seller_resp = await client.post(f"/api/v1/disputes/{dispute_id}/seller-evidence", json={
        "packing_video_url": "https://media.carvault.in/seller_packing_proof.mp4"
    }, headers=seller_headers)
    assert seller_resp.status_code == 200

    # 4. Admin inspects side-by-side comparison
    compare_resp = await client.get(f"/api/v1/disputes/admin/{dispute_id}/compare", headers=admin_headers)
    assert compare_resp.status_code == 200
    data = compare_resp.json()
    assert data["seller_packing_video"] == "https://media.carvault.in/seller_packing_proof.mp4"
    assert data["buyer_unboxing_video"] == "https://media.carvault.in/buyer_unboxing_proof.mp4"

    # 5. Admin resolves dispute in favor of buyer (REFUND_TO_BUYER)
    resolve_resp = await client.post(f"/api/v1/disputes/admin/{dispute_id}/resolve", json={
        "action": "REFUND_TO_BUYER",
        "admin_notes": "Unboxing video clearly proves continuous unboxing with damaged corner."
    }, headers=admin_headers)
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED_REFUNDED"

    # Order should now be REFUNDED
    await test_db.refresh(order)
    assert order.current_state == OrderState.REFUNDED

@pytest.mark.asyncio
async def test_universal_report_filing_and_fraud_priority(client, admin_token):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. File report for counterfeit die-cast (Must be tagged URGENT priority automatically)
    report_resp = await client.post("/api/v1/reports", json={
        "target_type": "LISTING",
        "target_id": "listing-fake-123",
        "reason": "FAKE_ITEM",
        "description": "Counterfeit wheel swap with fake tampo passed as genuine 1971 Super Treasure Hunt.",
        "evidence_url": "https://media.carvault.in/fake_proof.jpg",
        "contact_email": "informant@collectors.in"
    })
    assert report_resp.status_code == 201
    rep_data = report_resp.json()
    assert rep_data["reference_id"].startswith("REP-2026-")
    assert rep_data["priority"] == "URGENT"

    # 2. Admin retrieves queue and confirms priority
    queue_resp = await client.get("/api/v1/reports/admin/queue", headers=admin_headers)
    assert queue_resp.status_code == 200
    reports = queue_resp.json()
    assert len(reports) >= 1
    assert any(r["reference_id"] == rep_data["reference_id"] for r in reports)

@pytest.mark.asyncio
async def test_admin_enforcement_permanent_ban_and_device_blacklist(client, test_db, admin_token, seller_user):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Record a device fingerprint for the seller
    device = DeviceFingerprint(
        user_id=seller_user.id,
        device_hash="device_sha256_fraudster_hw01",
        is_blocked=False
    )
    test_db.add(device)
    await test_db.commit()

    # File report against seller profile
    report_resp = await client.post("/api/v1/reports", json={
        "target_type": "PROFILE",
        "target_id": seller_user.id,
        "reason": "OFF_PLATFORM_PAYMENT",
        "description": "Attempted to solicit off-platform direct UPI payment to avoid escrow.",
    })
    assert report_resp.status_code == 201
    ref_id = report_resp.json()["reference_id"]

    # Admin takes PERMANENT_BAN action
    # Query report object id
    from app.models.report import UserReport
    from sqlalchemy import select
    res = await test_db.execute(select(UserReport).where(UserReport.reference_id == ref_id))
    report_obj = res.scalars().first()

    ban_resp = await client.post(f"/api/v1/reports/admin/{report_obj.id}/enforce", json={
        "action": "PERMANENT_BAN",
        "admin_notes": "Confirmed off-platform payment chat solicitation. Permanent ban with device blacklist."
    }, headers=admin_headers)
    assert ban_resp.status_code == 200

    # Verify seller user is permanently banned and device is blacklisted
    await test_db.refresh(seller_user)
    assert seller_user.is_banned is True
    assert "Fraud Enforcement" in seller_user.ban_reason

    await test_db.refresh(device)
    assert device.is_blocked is True
