# Listing management, verification code generation, and automated media analysis
import random
import string
from io import BytesIO
import imagehash
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.listing import Listing, ListingMedia, ListingStatus, DiecastCatalog
from app.models.review import ReviewQueue
from app.models.user import User, KycTier

def generate_random_verification_code():
    # Generates a 7-character verification code like "CV-8R49K"
    chars = string.ascii_uppercase + string.digits
    random_str = "".join(random.choice(chars) for _ in range(5))
    return f"CV-{random_str}"

def compute_image_phash(image_bytes):
    # Computes 64-bit perceptual hash (pHash) to detect duplicate or stolen images across listings
    try:
        img = Image.open(BytesIO(image_bytes))
        h = imagehash.phash(img)
        return str(h)
    except Exception:
        # Fallback if bytes are invalid
        return None

async def create_new_listing(seller_id, listing_data, db: AsyncSession):
    # Verifies seller listing cap, saves listing, media, and queues for admin review
    user = await db.get(User, seller_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check seller's active listing cap
    active_count_stmt = select(func.count(Listing.id)).where(
        Listing.seller_id == seller_id,
        Listing.status.in_([ListingStatus.PENDING_REVIEW, ListingStatus.APPROVED])
    )
    count_res = await db.execute(active_count_stmt)
    current_active = count_res.scalar_one()

    cap = 3
    if user.trust_score:
        cap = user.trust_score.active_listing_cap
    if user.kyc_tier == KycTier.TIER_0_NEW and current_active >= cap:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Active listing cap reached ({cap} listings max for Tier 0 accounts). Complete KYC to list more."
        )

    # Ensure at least one image is marked as physical verification shot
    has_verification_shot = any(m.is_verification_shot for m in listing_data.media)
    if not has_verification_shot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one photo must show the handwritten verification code beside the car."
        )

    # Create listing record
    listing = Listing(
        seller_id=seller_id,
        title=listing_data.title,
        description=listing_data.description,
        series_name=listing_data.series_name,
        model_year=listing_data.model_year,
        toy_code=listing_data.toy_code,
        condition=listing_data.condition,
        tags=listing_data.tags,
        price_paise=listing_data.price_paise,
        verification_code=listing_data.verification_code,
        is_in_app_capture=listing_data.is_in_app_capture,
        status=ListingStatus.PENDING_REVIEW
    )
    db.add(listing)
    await db.flush()

    # Add media attachments
    for m in listing_data.media:
        media_rec = ListingMedia(
            listing_id=listing.id,
            media_url=m.media_url,
            media_type=m.media_type,
            is_verification_shot=m.is_verification_shot,
            phash_value=m.phash_value,
            display_order=m.display_order
        )
        db.add(media_rec)

    # Initialize review queue item
    review_item = ReviewQueue(
        listing_id=listing.id,
        auto_check_media_count_met=len(listing_data.media) >= 3,
        auto_check_flags=[]
    )

    # Perform automated duplicate pHash check against existing active listings
    duplicate_found = False
    for m in listing_data.media:
        if m.phash_value:
            dup_stmt = select(ListingMedia).join(Listing).where(
                Listing.seller_id != seller_id,
                Listing.status == ListingStatus.APPROVED,
                ListingMedia.phash_value == m.phash_value
            )
            dup_res = await db.execute(dup_stmt)
            if dup_res.scalars().first():
                duplicate_found = True
                break

    if duplicate_found:
        review_item.auto_check_phash_duplicate = True
        review_item.auto_check_flags.append("POTENTIAL_IMAGE_DUPLICATE_PHASH")

    # Automated price outlier check: check if price is far below known catalog minimum
    if listing_data.toy_code:
        cat_stmt = select(DiecastCatalog).where(DiecastCatalog.toy_code == listing_data.toy_code)
        cat_res = await db.execute(cat_stmt)
        catalog_entry = cat_res.scalars().first()
        if catalog_entry and catalog_entry.typical_market_min_paise:
            # If price is lower than 50% of typical market min, flag as price anomaly
            if listing_data.price_paise < (catalog_entry.typical_market_min_paise * 0.5):
                review_item.auto_check_price_outlier = True
                review_item.auto_check_flags.append("PRICE_FAR_BELOW_MARKET")

    db.add(review_item)
    await db.commit()
    await db.refresh(listing)
    return listing
