# Public API and agent-readable endpoints with schema.org structured data
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.listing import Listing, ListingStatus, DiecastCatalog
from app.models.user import User
from app.models.order import Order, OrderState

router = APIRouter()

@router.get("/search")
async def public_search(
    q: Optional[str] = Query(None, description="Search query by casting title, model name, or toy code"),
    series: Optional[str] = Query(None, description="Filter by series (e.g. Car Culture, Boulevard)"),
    max_price_inr: Optional[float] = None,
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db)
):
    # Agent-optimized search: Returns verified listings with seller trust scores
    stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.APPROVED)
        .options(
            selectinload(Listing.media),
            selectinload(Listing.seller).selectinload(User.trust_score)
        )
        .order_by(Listing.created_at.desc())
    )

    if q:
        stmt = stmt.where(Listing.title.ilike(f"%{q}%"))
    if series:
        stmt = stmt.where(Listing.series_name == series)
    if max_price_inr:
        stmt = stmt.where(Listing.price_paise <= int(max_price_inr * 100))

    stmt = stmt.limit(limit)
    res = await db.execute(stmt)
    listings = res.scalars().all()

    return {
        "count": len(listings),
        "results": [
            {
                "id": l.id,
                "title": l.title,
                "series_name": l.series_name,
                "model_year": l.model_year,
                "toy_code": l.toy_code,
                "condition": l.condition.value,
                "price_inr": l.price_paise / 100.0,
                "verification_code": l.verification_code,
                "is_in_app_capture": l.is_in_app_capture,
                "seller": {
                    "id": l.seller.id,
                    "name": l.seller.full_name or "Verified Collector",
                    "kyc_tier": l.seller.kyc_tier.value,
                    "trust_score": l.seller.trust_score.score if l.seller.trust_score else 50
                },
                "primary_image": l.media[0].media_url if l.media else None
            }
            for l in listings
        ]
    }

@router.get("/listings/{listing_id}")
async def public_listing_detail(listing_id: str, db: AsyncSession = Depends(get_db)):
    # Returns comprehensive listing details with schema.org Product and Offer JSON-LD metadata
    stmt = (
        select(Listing)
        .where(Listing.id == listing_id)
        .options(
            selectinload(Listing.media),
            selectinload(Listing.seller).selectinload(User.trust_score)
        )
    )
    res = await db.execute(stmt)
    listing = res.scalars().first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    seller = listing.seller
    score = seller.trust_score.score if seller and seller.trust_score else 50

    # schema.org Product & Offer markup
    json_ld = {
        "@context": "https://schema.org/",
        "@type": "Product",
        "name": listing.title,
        "image": [m.media_url for m in listing.media],
        "description": listing.description,
        "sku": listing.toy_code or f"CV-{listing.id[:8]}",
        "offers": {
            "@type": "Offer",
            "url": f"https://carvault.in/listings/{listing.id}",
            "priceCurrency": "INR",
            "price": listing.price_paise / 100.0,
            "itemCondition": f"https://schema.org/{'NewCondition' if listing.condition.value == 'MINT_CARD' else 'UsedCondition'}",
            "availability": f"https://schema.org/{'InStock' if listing.status == ListingStatus.APPROVED else 'OutOfStock'}"
        }
    }

    return {
        "id": listing.id,
        "title": listing.title,
        "description": listing.description,
        "series_name": listing.series_name,
        "model_year": listing.model_year,
        "toy_code": listing.toy_code,
        "condition": listing.condition.value,
        "price_inr": listing.price_paise / 100.0,
        "verification_code": listing.verification_code,
        "status": listing.status.value,
        "media": [{"url": m.media_url, "is_verification_shot": m.is_verification_shot} for m in listing.media],
        "seller": {
            "name": seller.full_name or "Verified Collector",
            "kyc_tier": seller.kyc_tier.value,
            "trust_score": score
        },
        "schema_org_json_ld": json_ld
    }

@router.get("/price-history/{series}/{toy_code}")
async def get_price_history(series: str, toy_code: str, db: AsyncSession = Depends(get_db)):
    # Returns valuation guide and past settled transaction data for collectors and AI pricing bots
    stmt = select(DiecastCatalog).where(DiecastCatalog.toy_code == toy_code)
    res = await db.execute(stmt)
    catalog = res.scalars().first()

    # Query completed orders for this casting
    order_stmt = (
        select(Order)
        .join(Listing)
        .where(
            Listing.toy_code == toy_code,
            Order.current_state == OrderState.RELEASED
        )
        .order_by(Order.released_at.desc())
        .limit(10)
    )
    order_res = await db.execute(order_stmt)
    settled_orders = order_res.scalars().all()

    return {
        "series": series,
        "toy_code": toy_code,
        "benchmark": {
            "estimated_mrp_inr": (catalog.estimated_mrp_paise / 100.0) if catalog and catalog.estimated_mrp_paise else None,
            "typical_market_min_inr": (catalog.typical_market_min_paise / 100.0) if catalog and catalog.typical_market_min_paise else None,
            "typical_market_max_inr": (catalog.typical_market_max_paise / 100.0) if catalog and catalog.typical_market_max_paise else None,
        },
        "recent_settled_sales": [
            {
                "order_id": o.id,
                "price_inr": o.item_price_paise / 100.0,
                "settled_at": o.released_at
            }
            for o in settled_orders
        ]
    }
