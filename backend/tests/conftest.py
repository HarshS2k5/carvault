# Pytest fixtures for async database sessions and authenticated HTTP test clients
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool
from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.models.user import User, UserRole, KycTier, UserTrustScore
from app.main import app

# In-memory async SQLite with StaticPool so all connections share the same memory DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def test_db(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

@pytest_asyncio.fixture
async def client(test_engine):
    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def seller_user(test_db):
    user = User(
        phone_number="+919876543210",
        full_name="Collector Aryan",
        role=UserRole.SELLER,
        kyc_tier=KycTier.TIER_0_NEW,
        is_active=True
    )
    test_db.add(user)
    await test_db.flush()

    trust = UserTrustScore(
        user_id=user.id,
        score=50,
        active_listing_cap=3,
        payout_hold_hours=48
    )
    test_db.add(trust)
    await test_db.commit()
    await test_db.refresh(user)
    return user

@pytest_asyncio.fixture
async def seller_token(seller_user):
    return create_access_token(subject=seller_user.id)

@pytest_asyncio.fixture
async def admin_user(test_db):
    admin = User(
        phone_number="+919999999999",
        full_name="Admin Moderator",
        role=UserRole.ADMIN,
        kyc_tier=KycTier.TIER_2_PRO,
        is_active=True
    )
    test_db.add(admin)
    await test_db.commit()
    await test_db.refresh(admin)
    return admin

@pytest_asyncio.fixture
async def admin_token(admin_user):
    return create_access_token(subject=admin_user.id)

@pytest_asyncio.fixture
async def buyer_user(test_db):
    buyer = User(
        phone_number="+919111111111",
        full_name="Collector Buyer Rohit",
        role=UserRole.BUYER,
        kyc_tier=KycTier.TIER_0_NEW,
        is_active=True
    )
    test_db.add(buyer)
    await test_db.flush()
    trust = UserTrustScore(user_id=buyer.id, score=50, active_listing_cap=3, payout_hold_hours=48)
    test_db.add(trust)
    await test_db.commit()
    await test_db.refresh(buyer)
    return buyer

@pytest_asyncio.fixture
async def buyer_token(buyer_user):
    return create_access_token(subject=buyer_user.id)

@pytest_asyncio.fixture
async def approved_listing(test_db, seller_user):
    from app.models.listing import Listing, ListingCondition, ListingStatus, ListingMedia
    listing = Listing(
        seller_id=seller_user.id,
        title="Datsun 240Z Car Culture Premium",
        description="Mint blister, pristine card and wheels.",
        series_name="Car Culture",
        model_year=2023,
        toy_code="HKC44",
        condition=ListingCondition.MINT_CARD,
        tags=["ORIGINAL", "SEALED"],
        price_paise=150000, # ₹1,500.00
        verification_code="CV-TEST88",
        status=ListingStatus.APPROVED
    )
    test_db.add(listing)
    await test_db.flush()
    media = ListingMedia(
        listing_id=listing.id,
        media_url="https://media.carvault.in/datsun.jpg",
        media_type="IMAGE",
        is_verification_shot=True,
        display_order=0
    )
    test_db.add(media)
    await test_db.commit()
    await test_db.refresh(listing)
    return listing

