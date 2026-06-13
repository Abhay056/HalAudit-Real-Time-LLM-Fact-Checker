"""
HalAudit - Real-Time LLM Fact-Checker Pipeline
FastAPI Application Entry Point
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from app.config import get_settings
from app.api.v1.router import router as v1_router
from app.api.middleware import RateLimitMiddleware
from app.db.audit_store import init_db, close_db
from app.db.redis_client import close_redis
from app.corpus.loader import load_seed_corpus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager — startup and shutdown hooks."""
    # === STARTUP ===
    logger.info("=" * 60)
    logger.info("  HalAudit - Real-Time LLM Fact-Checker Pipeline")
    logger.info("=" * 60)

    # Initialize audit database
    await init_db()
    logger.info("✓ Audit database initialized")

    # Load seed corpus into ChromaDB
    try:
        corpus_size = await load_seed_corpus()
        logger.info(f"✓ Corpus loaded: {corpus_size} documents")
    except Exception as e:
        logger.warning(f"⚠ Corpus loading failed (non-critical): {e}")

    # Pre-warm models (optional, improves first-request latency)
    try:
        from app.core.nli_scorer import get_nli_scorer
        scorer = get_nli_scorer()
        _ = scorer.model
        logger.info("✓ NLI model loaded")
    except Exception as e:
        logger.warning(f"⚠ NLI model pre-warming failed (will load on first request): {e}")

    settings = get_settings()
    logger.info(f"✓ Server ready on {settings.host}:{settings.port}")
    logger.info("=" * 60)

    yield

    # === SHUTDOWN ===
    logger.info("Shutting down HalAudit...")
    await close_db()
    await close_redis()
    logger.info("Goodbye!")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="HalAudit - Real-Time LLM Fact-Checker",
        description=(
            "A production-grade pipeline that audits LLM responses by extracting "
            "atomic claims, retrieving evidence via RAG, and scoring each claim "
            "using Natural Language Inference (NLI)."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # --- CORS Middleware ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Rate Limiting Middleware ---
    app.add_middleware(RateLimitMiddleware)

    # --- API Routes ---
    app.include_router(v1_router)

    # --- Dashboard Static Files ---
    dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
    if os.path.exists(dashboard_dir):
        app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")
        logger.info(f"Dashboard served from: {dashboard_dir}")

    # --- Root redirect to dashboard ---
    @app.get("/", include_in_schema=False)
    async def root():
        """Redirect root to dashboard."""
        return RedirectResponse(url="/dashboard/")

    return app


# Create the app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info",
    )
