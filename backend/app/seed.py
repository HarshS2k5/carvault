# Database seeder creating benchmark die-cast catalog and test demo accounts
import asyncio
from app.core.database import engine, Base, AsyncSessionLocal
from app.models.user import User, UserRole, KycTier, UserTrustScore
from app.models.listing import Listing, ListingCondition, ListingStatus, ListingMedia, DiecastCatalog
from app.models.review import ReviewQueue
from app.services.listing_service import generate_random_verification_code

async def seed_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        # 1. Admin Moderator Account
        admin = User(
            phone_number="+919999999999",
            full_name="CarVault Official Admin",
            email="admin@carvault.in",
            role=UserRole.ADMIN,
            kyc_tier=KycTier.TIER_2_PRO,
            is_active=True
        )
        session.add(admin)
        await session.flush()
        session.add(UserTrustScore(user_id=admin.id, score=100, active_listing_cap=999, payout_hold_hours=0))

        # 2. Verified Collector Seller Account
        seller = User(
            phone_number="+919876543210",
            full_name="Arjun Diecast Garage",
            email="arjun@diecastindia.com",
            role=UserRole.SELLER,
            kyc_tier=KycTier.TIER_1_VERIFIED,
            is_active=True
        )
        session.add(seller)
        await session.flush()
        session.add(UserTrustScore(user_id=seller.id, score=85, active_listing_cap=25, payout_hold_hours=24))

        # 3. Benchmark Catalog Reference Data (for market price anomaly auto-checks)
        catalog_items = [
            DiecastCatalog(
                series_name="Car Culture",
                model_name="Nissan Skyline GT-R (BNR34)",
                release_year=2023,
                toy_code="HKC34",
                estimated_mrp_paise=54900,         # ₹549 MRP
                typical_market_min_paise=120000,    # ₹1,200 min secondary
                typical_market_max_paise=180000     # ₹1,800 max secondary
            ),
            DiecastCatalog(
                series_name="Boulevard",
                model_name="Porsche 911 GT3 RS",
                release_year=2024,
                toy_code="GJT68",
                estimated_mrp_paise=54900,
                typical_market_min_paise=95000,
                typical_market_max_paise=150000
            ),
            DiecastCatalog(
                series_name="Mainlines",
                model_name="'71 Datsun 510 Wagon (Super Treasure Hunt)",
                release_year=2022,
                toy_code="HCW42",
                estimated_mrp_paise=17900,
                typical_market_min_paise=450000,    # ₹4,500 STH rarity
                typical_market_max_paise=700000
            ),
        ]
        session.add_all(catalog_items)

        # 4. An already approved live listing
        code1 = generate_random_verification_code()
        live_listing = Listing(
            seller_id=seller.id,
            title="Nissan Skyline GT-R R34 Car Culture - Mint Blister",
            description="Authentic Real Riders rubber tyres, flawless blister card. Kept in plastic protector case.",
            series_name="Car Culture",
            model_year=2023,
            toy_code="HKC34",
            condition=ListingCondition.MINT_CARD,
            tags=["ORIGINAL", "SEALED"],
            price_paise=145000, # ₹1,450.00
            verification_code=code1,
            is_in_app_capture=True,
            status=ListingStatus.APPROVED
        )
        session.add(live_listing)
        await session.flush()
        session.add(ListingMedia(
            listing_id=live_listing.id,
            media_url="https://images.unsplash.com/photo-1581235720704-06d3acfcb36f?w=800",
            media_type="IMAGE",
            is_verification_shot=True,
            phash_value="c4f1e0a8b9d3",
            display_order=0
        ))

        # 5. A pending listing waiting in Admin Review Queue
        code2 = generate_random_verification_code()
        pending_listing = Listing(
            seller_id=seller.id,
            title="Porsche 911 GT3 RS Boulevard Premium",
            description="Brand new card, verified casting code on baseplate.",
            series_name="Boulevard",
            model_year=2024,
            toy_code="GJT68",
            condition=ListingCondition.MINT_CARD,
            tags=["ORIGINAL", "SEALED"],
            price_paise=110000, # ₹1,100.00
            verification_code=code2,
            is_in_app_capture=False,
            status=ListingStatus.PENDING_REVIEW
        )
        session.add(pending_listing)
        await session.flush()
        session.add(ListingMedia(
            listing_id=pending_listing.id,
            media_url="https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800",
            media_type="IMAGE",
            is_verification_shot=True,
            phash_value="e8a7b4c2d1f9",
            display_order=0
        ))
        session.add(ReviewQueue(
            listing_id=pending_listing.id,
            auto_check_media_count_met=True,
            auto_check_phash_duplicate=False,
            auto_check_price_outlier=False,
            auto_check_flags=[]
        ))

        await session.commit()
        print("CarVault database seeded successfully with Admin, Seller, Catalog benchmarks, and demo listings.")

if __name__ == "__main__":
    asyncio.run(seed_data())
