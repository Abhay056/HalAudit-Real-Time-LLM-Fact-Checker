"""
HalAudit Async Tasks
ARQ task definitions for async claim processing via Redis queue.
"""

import json
import logging
import time
from typing import Optional, Dict, Any

from app.core.pipeline import get_audit_pipeline
from app.models.schemas import AuditOptions, AuditReport
from app.db.audit_store import save_audit

logger = logging.getLogger(__name__)


async def process_audit_job(
    ctx: Dict[str, Any],
    text: str,
    options_dict: Optional[Dict] = None,
    llm_prompt: Optional[str] = None,
) -> Dict:
    """
    ARQ task: Run the full audit pipeline on a text.
    
    Args:
        ctx: ARQ context (contains Redis connection).
        text: The text to audit.
        options_dict: Optional audit options as a dict.
        llm_prompt: Original LLM prompt if applicable.
        
    Returns:
        Serialized AuditReport as a dict.
    """
    job_id = ctx.get("job_id", "unknown")
    logger.info(f"Processing audit job: {job_id}")

    try:
        # Parse options
        options = AuditOptions(**options_dict) if options_dict else None

        # Run the pipeline
        pipeline = get_audit_pipeline()
        report = await pipeline.audit(text, options=options, llm_prompt=llm_prompt)

        # Persist the audit report
        try:
            await save_audit(report)
        except Exception as e:
            logger.warning(f"Failed to save audit to DB: {e}")

        # Store result in Redis with 1-hour TTL
        redis = ctx.get("redis")
        if redis:
            result_key = f"audit_result:{job_id}"
            await redis.set(
                result_key,
                report.model_dump_json(),
                ex=3600  # 1 hour TTL
            )

        logger.info(
            f"Audit job {job_id} completed: "
            f"trust_score={report.trust_score:.2%}, "
            f"claims={report.total_claims}"
        )

        return report.model_dump()

    except Exception as e:
        logger.error(f"Audit job {job_id} failed: {e}", exc_info=True)
        # Store error in Redis
        redis = ctx.get("redis")
        if redis:
            error_key = f"audit_result:{job_id}"
            await redis.set(
                error_key,
                json.dumps({"error": str(e), "status": "failed"}),
                ex=3600
            )
        raise


async def process_generate_and_audit_job(
    ctx: Dict[str, Any],
    prompt: str,
    options_dict: Optional[Dict] = None,
) -> Dict:
    """
    ARQ task: Generate an LLM response and then audit it.
    
    Args:
        ctx: ARQ context.
        prompt: User prompt to send to LLM.
        options_dict: Optional audit options.
        
    Returns:
        Serialized AuditReport as a dict.
    """
    job_id = ctx.get("job_id", "unknown")
    logger.info(f"Processing generate-and-audit job: {job_id}")

    try:
        options = AuditOptions(**options_dict) if options_dict else None
        pipeline = get_audit_pipeline()
        report = await pipeline.generate_and_audit(prompt, options=options)

        # Persist
        try:
            await save_audit(report)
        except Exception as e:
            logger.warning(f"Failed to save audit to DB: {e}")

        # Store result
        redis = ctx.get("redis")
        if redis:
            result_key = f"audit_result:{job_id}"
            await redis.set(
                result_key,
                report.model_dump_json(),
                ex=3600
            )

        logger.info(f"Generate-and-audit job {job_id} completed")
        return report.model_dump()

    except Exception as e:
        logger.error(f"Generate-and-audit job {job_id} failed: {e}", exc_info=True)
        redis = ctx.get("redis")
        if redis:
            error_key = f"audit_result:{job_id}"
            await redis.set(
                error_key,
                json.dumps({"error": str(e), "status": "failed"}),
                ex=3600
            )
        raise
