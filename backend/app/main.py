# CarVault FastAPI application entry point
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import auth, listings, review_queue, orders, webhooks, ledger, disputes, reports, public, mcp_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: clean up database connections
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Trust-First Collector Die-Cast Marketplace MVP for India with Escrow & Admin Verification",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend and local tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth & KYC"])
app.include_router(listings.router, prefix=f"{settings.API_V1_STR}/listings", tags=["Listings"])
app.include_router(review_queue.router, prefix=f"{settings.API_V1_STR}/admin/review-queue", tags=["Admin Review Queue"])
app.include_router(orders.router, prefix=f"{settings.API_V1_STR}/orders", tags=["Orders & Escrow"])
app.include_router(webhooks.router, prefix=f"{settings.API_V1_STR}/payments/webhooks", tags=["Payment Webhooks"])
app.include_router(ledger.router, prefix=f"{settings.API_V1_STR}/admin/ledger", tags=["Admin Ledger & Recon"])
app.include_router(disputes.router, prefix=f"{settings.API_V1_STR}/disputes", tags=["Disputes & Claims"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Universal Reports"])
app.include_router(public.router, prefix=f"{settings.API_V1_STR}/public", tags=["Public & AI Agents"])
app.include_router(mcp_routes.router, prefix=f"{settings.API_V1_STR}/mcp", tags=["MCP AI Tools"])

@app.get("/health")
def health_check():
    # Simple liveness check
    return {"status": "ok", "app": settings.PROJECT_NAME, "version": "1.0.0"}
