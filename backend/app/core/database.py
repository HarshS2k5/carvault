# Database connection and async session management
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import settings

# Create async engine supporting SQLite and PostgreSQL asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    # Dependency for FastAPI endpoints yielding an isolated DB session
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
