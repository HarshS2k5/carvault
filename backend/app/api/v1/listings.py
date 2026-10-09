# Listings API endpoints for marketplace buyers and sellers
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.listing import Listing, ListingStatus, ListingCondition
from app.schemas.listing import (
    VerificationCodeResponse, ListingCreate,
    ListingResponse, ListingDetailResponse
)
from app.services.listing_service import generate_random_verification_code, create_new_listing

router = APIRouter()

@router.get("/generate-code", response_model=VerificationCodeResponse)
def get_verification_code():
    # Returns a random code seller must write on paper and place beside car in photo
    code = generate_random_verification_code()
    return VerificationCodeResponse(verification_code=code)

@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: ListingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Submits die-cast car listing and places it into the Admin Review Queue
    listing = await create_new_listing(
        seller_id=current_user.id,
        listing_data=payload,
        db=db
    )
    # Eagerly load media for response
    stmt = select(Listing).where(Listing.id == listing.id).options(selectinload(Listing.media))
    res = await db.execute(stmt)
    full_listing = res.scalar_one()

    return ListingResponse(
        id=full_listing.id,
        seller_id=full_listing.seller_id,
        title=full_listing.title,
        description=full_listing.description,
        series_name=full_listing.series_name,
        model_year=full_listing.model_year,
        toy_code=full_listing.toy_code,
        condition=full_listing.condition,
        tags=full_listing.tags,
        price_paise=full_listing.price_paise,
        price_rupees=full_listing.price_paise / 100.0,
        verification_code=full_listing.verification_code,
        is_in_app_capture=full_listing.is_in_app_capture,
        status=full_listing.status,
        created_at=full_listing.created_at,
        media=full_listing.media
    )

@router.get("", response_model=List[ListingResponse])
async def list_approved_listings(
    q: Optional[str] = Query(None, description="Search term for title or series"),
    series: Optional[str] = Query(None, description="Filter by series name"),
    condition: Optional[ListingCondition] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    # Public marketplace search: STRICTLY returns APPROVED listings only
    stmt = (
        select(Listing)
        .where(Listing.status == ListingStatus.APPROVED)
        .options(selectinload(Listing.media))
        .order_by(Listing.created_at.desc())
    )

    if q:
        stmt = stmt.where(Listing.title.ilike(f"%{q}%"))
    if series:
        stmt = stmt.where(Listing.series_name == series)
    if condition:
        stmt = stmt.where(Listing.condition == condition)
    if min_year:
        stmt = stmt.where(Listing.model_year >= min_year)
    if max_year:
        stmt = stmt.where(Listing.model_year <= max_year)

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    listings = res.scalars().all()

    return [
        ListingResponse(
            id=item.id,
            seller_id=item.seller_id,
            title=item.title,
            description=item.description,
            series_name=item.series_name,
            model_year=item.model_year,
            toy_code=item.toy_code,
            condition=item.condition,
            tags=item.tags,
            price_paise=item.price_paise,
            price_rupees=item.price_paise / 100.0,
            verification_code=item.verification_code,
            is_in_app_capture=item.is_in_app_capture,
            status=item.status,
            created_at=item.created_at,
            media=item.media
        )
        for item in listings
    ]

@router.get("/{listing_id}", response_model=ListingDetailResponse)
async def get_listing_detail(listing_id: str, db: AsyncSession = Depends(get_db)):
    # Returns public details, physical proof media, and seller trust metrics
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

    return ListingDetailResponse(
        id=listing.id,
        seller_id=listing.seller_id,
        title=listing.title,
        description=listing.description,
        series_name=listing.series_name,
        model_year=listing.model_year,
        toy_code=listing.toy_code,
        condition=listing.condition,
        tags=listing.tags,
        price_paise=listing.price_paise,
        price_rupees=listing.price_paise / 100.0,
        verification_code=listing.verification_code,
        is_in_app_capture=listing.is_in_app_capture,
        status=listing.status,
        created_at=listing.created_at,
        media=listing.media,
        seller_name=seller.full_name or "Anonymous Collector",
        seller_kyc_tier=seller.kyc_tier.value if seller else None,
        seller_trust_score=score
    )
