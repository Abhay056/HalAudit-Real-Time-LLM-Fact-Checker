"""
HalAudit ARQ Worker
Worker settings and lifecycle hooks for the async task queue.
"""

import logging
from arq import cron
from arq.connections import RedisSettings

from app.config import get_settings
from app.queue.tasks import process_audit_job, process_generate_and_audit_job

logger = logging.getLogger(__name__)


async def startup(ctx):
    """Worker startup hook — preload models."""
    logger.info("ARQ Worker starting up...")

    # Preload the NLI model so first job doesn't have cold-start latency
    try:
        from app.core.nli_scorer import get_nli_scorer
        scorer = get_nli_scorer()
        _ = scorer.model  # Trigger lazy load
        logger.info("NLI model preloaded")
    except Exception as e:
        logger.warning(f"Failed to preload NLI model: {e}")

    # Initialize the corpus
    try:
        from app.corpus.loader import load_seed_corpus
        await load_seed_corpus()
        logger.info("Seed corpus loaded")
    except Exception as e:
        logger.warning(f"Failed to load seed corpus: {e}")

    # Initialize audit DB
    try:
        from app.db.audit_store import init_db
        await init_db()
        logger.info("Audit database initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize audit DB: {e}")

    logger.info("ARQ Worker ready")


async def shutdown(ctx):
    """Worker shutdown hook — cleanup resources."""
    logger.info("ARQ Worker shutting down...")
    try:
        from app.db.audit_store import close_db
        await close_db()
    except Exception:
        pass
    logger.info("ARQ Worker stopped")


def get_worker_settings():
    """Build ARQ WorkerSettings from config."""
    settings = get_settings()

    # Parse Redis URL into RedisSettings
    redis_url = settings.redis_url
    # Default: redis://localhost:6379
    host = "localhost"
    port = 6379

    if "://" in redis_url:
        parts = redis_url.split("://")[1]
        if ":" in parts:
            host_port = parts.split("/")[0]
            host = host_port.split(":")[0]
            port = int(host_port.split(":")[1])

    return {
        "redis_settings": RedisSettings(host=host, port=port),
        "functions": [process_audit_job, process_generate_and_audit_job],
        "on_startup": startup,
        "on_shutdown": shutdown,
        "max_jobs": 10,
        "job_timeout": 300,  # 5 minutes max per job
        "retry_jobs": True,
        "max_tries": 3,
    }


class WorkerSettings:
    """ARQ Worker settings class for `arq worker app.queue.worker.WorkerSettings`."""

    _config = get_worker_settings()

    redis_settings = _config["redis_settings"]
    functions = _config["functions"]
    on_startup = _config["on_startup"]
    on_shutdown = _config["on_shutdown"]
    max_jobs = 10
    job_timeout = 300
    retry_jobs = True
    max_tries = 3
