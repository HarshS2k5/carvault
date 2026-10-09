# Tests covering Mobile OTP authentication, KYC submissions, and Penny-drop verification
import pytest

@pytest.mark.asyncio
async def test_otp_flow_and_me_endpoint(client):
    # 1. Request OTP for Indian phone number
    resp = await client.post("/api/v1/auth/otp/send", json={"phone_number": "+919876543210"})
    assert resp.status_code == 200
    assert "OTP dispatched" in resp.json()["message"]

    # 2. Verify OTP code
    verify_resp = await client.post("/api/v1/auth/otp/verify", json={
        "phone_number": "+919876543210",
        "otp_code": "123456",
        "device_hash": "test_device_hash_001"
    })
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert "access_token" in data
    token = data["access_token"]

    # 3. Access /me profile endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    profile = me_resp.json()
    assert profile["phone_number"] == "+919876543210"
    assert profile["kyc_tier"] == "TIER_0_NEW"
    assert profile["trust_score"] == 50

@pytest.mark.asyncio
async def test_kyc_pan_and_penny_drop(client, seller_user, seller_token):
    headers = {"Authorization": f"Bearer {seller_token}"}

    # 1. Submit PAN card
    pan_payload = {
        "pan_number": "ABCDE1234F",
        "full_name_as_per_pan": "Collector Aryan"
    }
    pan_resp = await client.post("/api/v1/auth/kyc/pan", json=pan_payload, headers=headers)
    assert pan_resp.status_code == 200
    assert pan_resp.json()["masked_pan"] == "ABCDE****F"

    # 2. Submit bank account for penny-drop name matching
    bank_payload = {
        "account_number": "987654321098",
        "ifsc_code": "HDFC0001234"
    }
    bank_resp = await client.post("/api/v1/auth/kyc/penny-drop", json=bank_payload, headers=headers)
    assert bank_resp.status_code == 200
    res_data = bank_resp.json()
    assert res_data["is_successful"] is True
    assert res_data["name_match_score"] >= 80.0

    # 3. Verify user promoted to Tier 1 Verified with updated listing cap
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["kyc_tier"] == "TIER_1_VERIFIED"
