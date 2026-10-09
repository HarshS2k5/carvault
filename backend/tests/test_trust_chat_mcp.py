# Tests for Trust scoring, Chat anti-leak filters, Public API, and MCP Agent tools
import pytest
from app.models.user import KycTier, DeviceFingerprint
from app.services.trust_score_service import calculate_and_update_trust_score, detect_account_anomalies
from app.services.chat_service import sanitize_chat_message, record_chat_leak_penalty

@pytest.mark.asyncio
async def test_trust_score_and_listing_cap_calculation(test_db, seller_user):
    # Tier 0 seller has baseline 50
    trust = await calculate_and_update_trust_score(seller_user.id, test_db)
    assert trust.score == 50
    assert trust.active_listing_cap == 3
    assert trust.payout_hold_hours == 48

    # Promote to Tier 1 Verified and complete 5 orders
    seller_user.kyc_tier = KycTier.TIER_1_VERIFIED
    trust.completed_orders = 5
    await test_db.commit()

    updated_trust = await calculate_and_update_trust_score(seller_user.id, test_db)
    # 50 base + 25 (Tier 1) + 10 (5 deals * 2) = 85
    assert updated_trust.score == 85
    assert updated_trust.active_listing_cap == 25
    assert updated_trust.payout_hold_hours == 24

@pytest.mark.asyncio
async def test_shared_device_anomaly_detection(test_db, seller_user, buyer_user):
    # Assign same device hash to two different user accounts
    shared_hash = "shared_device_hash_cybercafe_01"
    d1 = DeviceFingerprint(user_id=seller_user.id, device_hash=shared_hash)
    d2 = DeviceFingerprint(user_id=buyer_user.id, device_hash=shared_hash)
    test_db.add_all([d1, d2])
    await test_db.commit()

    flags = await detect_account_anomalies(seller_user.id, test_db)
    assert "SHARED_DEVICE_MULTI_ACCOUNT" in flags
    await test_db.refresh(seller_user.trust_score)
    assert "SHARED_DEVICE_MULTI_ACCOUNT" in seller_user.trust_score.risk_flags

def test_chat_sanitization_and_leak_censoring():
    # 1. Phone number leak attempt
    res1 = sanitize_chat_message("Bro please WhatsApp me on +919876543210 for price")
    assert res1["has_violation"] is True
    assert "PHONE_NUMBER" in res1["violations"]
    assert "+919876543210" not in res1["sanitized_text"]
    assert "[CENSORED: Phone numbers prohibited on CarVault]" in res1["sanitized_text"]

    # 2. UPI ID leak attempt
    res2 = sanitize_chat_message("Send ₹1200 directly to collector@okhdfcbank to skip fee")
    assert res2["has_violation"] is True
    assert "UPI_HANDLE" in res2["violations"]
    assert "collector@okhdfcbank" not in res2["sanitized_text"]
    assert "[CENSORED: Direct UPI payments prohibited]" in res2["sanitized_text"]

    # 3. External link leak attempt
    res3 = sanitize_chat_message("Check out my car collection at https://mycars.in/album")
    assert res3["has_violation"] is True
    assert "EXTERNAL_LINK" in res3["violations"]
    assert "https://mycars.in/album" not in res3["sanitized_text"]

    # 4. Clean communication
    res4 = sanitize_chat_message("Can you confirm if the blister has any soft corners?")
    assert res4["has_violation"] is False
    assert res4["sanitized_text"] == "Can you confirm if the blister has any soft corners?"

@pytest.mark.asyncio
async def test_public_api_and_mcp_tools(client, approved_listing):
    # 1. Test Public Search API
    search_resp = await client.get("/api/v1/public/search?series=Car+Culture")
    assert search_resp.status_code == 200
    search_json = search_resp.json()
    assert search_json["count"] >= 1
    item = search_json["results"][0]
    assert item["title"] == approved_listing.title
    assert "seller" in item
    assert "trust_score" in item["seller"]

    # 2. Test Public Detail API with schema.org JSON-LD
    detail_resp = await client.get(f"/api/v1/public/listings/{approved_listing.id}")
    assert detail_resp.status_code == 200
    detail_json = detail_resp.json()
    assert "schema_org_json_ld" in detail_json
    assert detail_json["schema_org_json_ld"]["@type"] == "Product"
    assert detail_json["schema_org_json_ld"]["offers"]["priceCurrency"] == "INR"

    # 3. Test MCP Tool: search_diecasts
    mcp_search = await client.post("/api/v1/mcp/tools/call", json={
        "tool_name": "search_diecasts",
        "arguments": {"series": "Car Culture"}
    })
    assert mcp_search.status_code == 200
    assert len(mcp_search.json()["matches"]) >= 1

    # 4. Test MCP Tool: create_purchase_intent (verifying human-in-the-loop requirement)
    mcp_intent = await client.post("/api/v1/mcp/tools/call", json={
        "tool_name": "create_purchase_intent",
        "arguments": {"listing_id": approved_listing.id, "buyer_phone": "+919111111111"}
    })
    assert mcp_intent.status_code == 200
    intent_data = mcp_intent.json()
    assert intent_data["status"] == "AWAITING_HUMAN_PAYMENT_CONFIRMATION"
    assert "human_checkout_url" in intent_data
    assert "prohibited by RBI" in intent_data["policy"]
