"""
HalAudit API v1 Router
All REST API endpoints for the hallucination audit pipeline.
"""

import json
import logging
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import Settings
from app.api.v1.dependencies import get_app_settings, check_redis_available, get_optional_redis
from app.models.schemas import (
    AuditRequest,
    AuditReport,
    AuditStatusResponse,
    AuditOptions,
    GenerateAndAuditRequest,
    CorpusIngestRequest,
    CorpusIngestResponse,
    HealthResponse,
    AuditHistoryQuery,
    AuditHistoryResponse,
)
from app.core.pipeline import get_audit_pipeline
from app.core.rag_retriever import get_rag_retriever
from app.db.audit_store import save_audit, get_audit, get_audit_history, get_stats
from app.db.redis_client import redis_health_check

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["HalAudit v1"])


# ──────────────────────────────────────────
# Health & Status
# ──────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint — exempt from rate limiting."""
    redis_status = await redis_health_check()
    retriever = get_rag_retriever()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        components={
            "api": "healthy",
            "redis": redis_status.get("status", "unknown"),
            "corpus_size": str(retriever.get_corpus_size()),
        }
    )


@router.get("/stats")
async def get_audit_stats():
    """Get aggregate audit statistics."""
    stats = await get_stats()
    corpus_size = get_rag_retriever().get_corpus_size()
    stats["corpus_size"] = corpus_size
    return stats


# ──────────────────────────────────────────
# Synchronous Audit
# ──────────────────────────────────────────

@router.post("/audit", response_model=AuditReport)
async def audit_text(request: AuditRequest):
    """
    Synchronous audit — processes the text and returns the full report.
    This endpoint waits for the pipeline to complete before responding.
    """
    try:
        pipeline = get_audit_pipeline()
        report = await pipeline.audit(
            text=request.text,
            options=request.options,
        )

        # Persist to audit log
        try:
            await save_audit(report)
        except Exception as e:
            logger.warning(f"Failed to save audit log: {e}")

        return report

    except Exception as e:
        logger.error(f"Audit failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Audit pipeline error: {str(e)}")


# ──────────────────────────────────────────
# Async Audit (Redis Queue)
# ──────────────────────────────────────────

@router.post("/audit/async", response_model=AuditStatusResponse)
async def audit_text_async(
    request: AuditRequest,
    redis=Depends(get_optional_redis),
):
    """
    Async audit — enqueues the job and returns a job ID immediately.
    Poll GET /api/v1/audit/{job_id} to get the result.
    Falls back to synchronous processing if Redis is unavailable.
    """
    if redis is None:
        # Fallback: run synchronously
        logger.info("Redis unavailable, falling back to synchronous audit")
        pipeline = get_audit_pipeline()
        report = await pipeline.audit(text=request.text, options=request.options)
        try:
            await save_audit(report)
        except Exception as e:
            logger.warning(f"Failed to save audit log: {e}")
        return AuditStatusResponse(
            job_id=report.id,
            status="completed",
            result=report,
            created_at=report.timestamp,
        )

    try:
        from arq.connections import ArqRedis, create_pool, RedisSettings
        from app.config import get_settings

        settings = get_settings()

        # Parse Redis URL
        redis_url = settings.redis_url
        host = "localhost"
        port = 6379
        if "://" in redis_url:
            parts = redis_url.split("://")[1]
            if ":" in parts:
                host_port = parts.split("/")[0]
                host = host_port.split(":")[0]
                port = int(host_port.split(":")[1])

        pool = await create_pool(RedisSettings(host=host, port=port))

        options_dict = request.options.model_dump() if request.options else None

        job = await pool.enqueue_job(
            "process_audit_job",
            request.text,
            options_dict,
            None,  # llm_prompt
        )

        await pool.close()

        return AuditStatusResponse(
            job_id=job.job_id,
            status="pending",
            created_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.warning(f"Failed to enqueue async job: {e}. Falling back to sync.")
        pipeline = get_audit_pipeline()
        report = await pipeline.audit(text=request.text, options=request.options)
        try:
            await save_audit(report)
        except Exception as db_err:
            logger.warning(f"Failed to save audit log: {db_err}")
        return AuditStatusResponse(
            job_id=report.id,
            status="completed",
            result=report,
            created_at=report.timestamp,
        )


# ──────────────────────────────────────────
# Audit History
# ──────────────────────────────────────────

@router.get("/audit/history", response_model=AuditHistoryResponse)
async def list_audit_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    min_trust_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    max_trust_score: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    has_contradictions: Optional[bool] = Query(default=None),
):
    """Get paginated audit history with optional filters."""
    try:
        query = AuditHistoryQuery(
            limit=limit,
            offset=offset,
            min_trust_score=min_trust_score,
            max_trust_score=max_trust_score,
            has_contradictions=has_contradictions,
        )
        return await get_audit_history(query)
    except Exception as e:
        logger.error(f"Audit history query failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query error: {str(e)}")


@router.get("/audit/{job_id}", response_model=AuditStatusResponse)
async def get_audit_status(
    job_id: str,
    redis=Depends(get_optional_redis),
):
    """
    Get the status/result of an async audit job.
    First checks Redis for the result, then falls back to the database.
    """
    # Check Redis first
    if redis:
        try:
            result_key = f"audit_result:{job_id}"
            result_json = await redis.get(result_key)

            if result_json:
                data = json.loads(result_json)

                # Check if it's an error
                if "error" in data and "status" in data and data["status"] == "failed":
                    return AuditStatusResponse(
                        job_id=job_id,
                        status="failed",
                        error=data["error"],
                    )

                # It's a successful result
                report = AuditReport.model_validate(data)
                return AuditStatusResponse(
                    job_id=job_id,
                    status="completed",
                    result=report,
                )

            # Check if job is still in queue
            from arq.connections import create_pool, RedisSettings
            from arq.jobs import Job

            settings = get_settings()
            redis_url = settings.redis_url
            host = "localhost"
            port = 6379
            if "://" in redis_url:
                parts = redis_url.split("://")[1]
                if ":" in parts:
                    host_port = parts.split("/")[0]
                    host = host_port.split(":")[0]
                    port = int(host_port.split(":")[1])

            pool = await create_pool(RedisSettings(host=host, port=port))
            job = Job(job_id=job_id, redis=pool)
            status = await job.status()
            await pool.close()

            status_map = {
                "deferred": "pending",
                "queued": "pending",
                "in_progress": "processing",
                "complete": "completed",
                "not_found": "not_found",
            }

            return AuditStatusResponse(
                job_id=job_id,
                status=status_map.get(str(status), "unknown"),
            )
        except Exception as e:
            logger.warning(f"Error checking Redis for job {job_id}: {e}")

    # Fallback: check database
    report = await get_audit(job_id)
    if report:
        return AuditStatusResponse(
            job_id=job_id,
            status="completed",
            result=report,
        )

    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")



# ──────────────────────────────────────────
# Generate and Audit
# ──────────────────────────────────────────

@router.post("/generate-and-audit", response_model=AuditReport)
async def generate_and_audit(request: GenerateAndAuditRequest):
    """
    Generate an LLM response from a prompt, then audit it.
    Requires OPENAI_API_KEY to be configured.
    """
    try:
        pipeline = get_audit_pipeline()
        report = await pipeline.generate_and_audit(
            prompt=request.prompt,
            options=request.options,
        )

        try:
            await save_audit(report)
        except Exception as e:
            logger.warning(f"Failed to save audit log: {e}")

        return report

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generate-and-audit failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


# ──────────────────────────────────────────
# Corpus Management
# ──────────────────────────────────────────

@router.post("/corpus/ingest", response_model=CorpusIngestResponse)
async def ingest_corpus(request: CorpusIngestRequest):
    """Add documents to the trusted corpus."""
    try:
        retriever = get_rag_retriever()
        ingested = await retriever.ingest(
            texts=request.texts,
            metadata=request.metadata,
            source=request.source,
        )

        total = retriever.get_corpus_size()

        return CorpusIngestResponse(
            ingested_count=ingested,
            total_corpus_size=total,
            message=f"Successfully ingested {ingested} documents.",
        )
    except Exception as e:
        logger.error(f"Corpus ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")


