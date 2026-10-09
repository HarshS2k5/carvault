# Tests for listing creation, physical verification shot enforcement, and Admin Review Queue
import pytest

@pytest.mark.asyncio
async def test_verification_code_and_listing_creation(client, seller_token):
    headers = {"Authorization": f"Bearer {seller_token}"}

    # 1. Fetch physical verification code
    code_resp = await client.get("/api/v1/listings/generate-code")
    assert code_resp.status_code == 200
    code = code_resp.json()["verification_code"]
    assert code.startswith("CV-")

    # 2. Try creating listing WITHOUT verification shot -> must fail
    invalid_payload = {
        "title": "Nissan Skyline GT-R R34 Boulevard",
        "description": "Mint on unbent card, real riders rubber wheels.",
        "series_name": "Boulevard",
        "model_year": 2023,
        "toy_code": "HKC34",
        "condition": "MINT_CARD",
        "tags": ["ORIGINAL", "SEALED"],
        "price_paise": 125000, # ₹1,250.00
        "verification_code": code,
        "is_in_app_capture": False,
        "media": [
            {
                "media_url": "https://media.carvault.in/img1.jpg",
                "media_type": "IMAGE",
                "is_verification_shot": False,
                "display_order": 0
            }
        ]
    }
    fail_resp = await client.post("/api/v1/listings", json=invalid_payload, headers=headers)
    assert fail_resp.status_code == 400
    assert "handwritten verification code" in fail_resp.json()["detail"]

    # 3. Create listing WITH verification shot -> succeeds into PENDING_REVIEW
    valid_payload = invalid_payload.copy()
    valid_payload["media"] = [
        {
            "media_url": "https://media.carvault.in/front.jpg",
            "media_type": "IMAGE",
            "is_verification_shot": False,
            "display_order": 0
        },
        {
            "media_url": "https://media.carvault.in/proof.jpg",
            "media_type": "IMAGE",
            "is_verification_shot": True, # Photo with paper showing code
            "phash_value": "a1b2c3d4e5f60718",
            "display_order": 1
        },
        {
            "media_url": "https://media.carvault.in/back.jpg",
            "media_type": "IMAGE",
            "is_verification_shot": False,
            "display_order": 2
        }
    ]
    create_resp = await client.post("/api/v1/listings", json=valid_payload, headers=headers)
    assert create_resp.status_code == 201
    listing = create_resp.json()
    assert listing["status"] == "PENDING_REVIEW"
    assert listing["price_rupees"] == 1250.0

    # 4. Confirm it does NOT appear in public marketplace search yet
    public_resp = await client.get("/api/v1/listings")
    assert public_resp.status_code == 200
    assert len(public_resp.json()) == 0

@pytest.mark.asyncio
async def test_admin_review_queue_and_approval(client, seller_token, admin_token):
    seller_headers = {"Authorization": f"Bearer {seller_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Seller creates listing
    payload = {
        "title": "Porsche 911 GT3 RS Car Culture",
        "description": "Pristine card, no soft corners.",
        "series_name": "Car Culture",
        "model_year": 2024,
        "toy_code": "FYN34",
        "condition": "MINT_CARD",
        "tags": ["ORIGINAL", "SEALED"],
        "price_paise": 85000,
        "verification_code": "CV-TEST1",
        "is_in_app_capture": True,
        "media": [
            {
                "media_url": "https://media.carvault.in/proof.jpg",
                "media_type": "IMAGE",
                "is_verification_shot": True,
                "phash_value": "ff00aa1122334455",
                "display_order": 0
            }
        ]
    }
    create_resp = await client.post("/api/v1/listings", json=payload, headers=seller_headers)
    assert create_resp.status_code == 201
    listing_id = create_resp.json()["id"]

    # 2. Admin inspects review queue
    queue_resp = await client.get("/api/v1/admin/review-queue", headers=admin_headers)
    assert queue_resp.status_code == 200
    queue_items = queue_resp.json()
    assert len(queue_items) >= 1
    target_review = next(item for item in queue_items if item["listing_id"] == listing_id)
    review_id = target_review["id"]

    # 3. Attempt approval without checking verification code -> must fail
    bad_approve_payload = {
        "reviewer_notes": "Looks nice",
        "checklist": {
            "checklist_code_matched": False,
            "checklist_tamper_packaging_checked": True,
            "checklist_media_clarity_checked": True,
            "checklist_condition_matches_desc": True
        }
    }
    fail_approve = await client.post(
        f"/api/v1/admin/review-queue/{review_id}/approve",
        json=bad_approve_payload,
        headers=admin_headers
    )
    assert fail_approve.status_code == 400
    assert "verification code match must be confirmed" in fail_approve.json()["detail"]

    # 4. Valid approval with verified code
    good_approve_payload = {
        "reviewer_notes": "Physical verification code matched. Blister intact.",
        "checklist": {
            "checklist_code_matched": True,
            "checklist_tamper_packaging_checked": True,
            "checklist_media_clarity_checked": True,
            "checklist_condition_matches_desc": True
        }
    }
    good_approve = await client.post(
        f"/api/v1/admin/review-queue/{review_id}/approve",
        json=good_approve_payload,
        headers=admin_headers
    )
    assert good_approve.status_code == 200
    assert good_approve.json()["status"] == "APPROVED"

    # 5. Public search now yields the approved listing!
    public_resp = await client.get("/api/v1/listings")
    assert public_resp.status_code == 200
    active_items = public_resp.json()
    assert len(active_items) == 1
    assert active_items[0]["id"] == listing_id
    assert active_items[0]["title"] == "Porsche 911 GT3 RS Car Culture"
