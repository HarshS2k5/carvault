# Model Context Protocol (MCP) tool implementations for autonomous collector agents
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.listing import Listing, ListingStatus, DiecastCatalog
from app.models.user import User

async def mcp_search_diecasts(
    query: str = None,
    series: str = None,
    max_price_inr: float = None,
    db: AsyncSession = None
) -> dict:
    # MCP Tool: Allows collector AI agents to search verified listings
    stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.APPROVED)
        .options(selectinload(Listing.media), selectinload(Listing.seller))
    )
    if query:
        stmt = stmt.where(Listing.title.ilike(f"%{query}%"))
    if series:
        stmt = stmt.where(Listing.series_name == series)
    if max_price_inr:
        stmt = stmt.where(Listing.price_paise <= int(max_price_inr * 100))

    res = await db.execute(stmt.limit(10))
    listings = res.scalars().all()

    return {
        "tool": "search_diecasts",
        "matches": [
            {
                "listing_id": l.id,
                "title": l.title,
                "series": l.series_name,
                "model_year": l.model_year,
                "price_inr": l.price_paise / 100.0,
                "condition": l.condition.value,
                "verification_code": l.verification_code,
                "seller_id": l.seller.id,
                "seller_name": l.seller.full_name or "Verified Collector"
            }
            for l in listings
        ]
    }

async def mcp_get_price_guide(toy_code: str, db: AsyncSession = None) -> dict:
    # MCP Tool: Retrieves pricing benchmarks for valuation estimation
    stmt = select(DiecastCatalog).where(DiecastCatalog.toy_code == toy_code)
    res = await db.execute(stmt)
    cat = res.scalars().first()

    if not cat:
        return {"error": f"No benchmark data found for casting code {toy_code}"}

    return {
        "tool": "get_price_guide",
        "toy_code": cat.toy_code,
        "model_name": cat.model_name,
        "series_name": cat.series_name,
        "mrp_inr": (cat.estimated_mrp_paise / 100.0) if cat.estimated_mrp_paise else None,
        "fair_market_min_inr": (cat.typical_market_min_paise / 100.0) if cat.typical_market_min_paise else None,
        "fair_market_max_inr": (cat.typical_market_max_paise / 100.0) if cat.typical_market_max_paise else None
    }

async def mcp_verify_seller_trust(seller_id: str, db: AsyncSession = None) -> dict:
    # MCP Tool: Evaluates seller credibility, dispute rate, and KYC tier
    user = await db.get(User, seller_id)
    if not user:
        return {"error": "Seller account not found"}

    score = user.trust_score.score if user.trust_score else 50
    return {
        "tool": "verify_seller_trust",
        "seller_id": user.id,
        "name": user.full_name or "Collector",
        "kyc_tier": user.kyc_tier.value,
        "trust_score": score,
        "is_trust_level_high": score >= 75,
        "completed_deals": user.trust_score.completed_orders if user.trust_score else 0,
        "is_banned": user.is_banned
    }

async def mcp_create_purchase_intent(listing_id: str, buyer_phone: str, db: AsyncSession = None) -> dict:
    # MCP Tool: AI agents can create purchase intent, but PAYMENT ALWAYS REQUIRES HUMAN CONFIRMATION
    listing = await db.get(Listing, listing_id)
    if not listing:
        return {"error": "Listing not found"}
    if listing.status != ListingStatus.APPROVED:
        return {"error": "Listing is no longer available"}

    return {
        "tool": "create_purchase_intent",
        "listing_id": listing.id,
        "title": listing.title,
        "amount_inr": listing.price_paise / 100.0,
        "status": "AWAITING_HUMAN_PAYMENT_CONFIRMATION",
        "human_checkout_url": f"https://carvault.in/orders/checkout?listing_id={listing.id}",
        "policy": "Autonomous payments without human OTP/biometric approval are prohibited by RBI payment rules."
    }
