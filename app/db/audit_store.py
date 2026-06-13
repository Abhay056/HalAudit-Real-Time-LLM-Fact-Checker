"""
HalAudit Audit Store
SQLite-based persistent storage for audit logs with filtering.
"""

import json
import logging
import aiosqlite
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.config import get_settings
from app.models.schemas import AuditReport, AuditHistoryQuery, AuditHistoryResponse

logger = logging.getLogger(__name__)

# Global database connection
_db: Optional[aiosqlite.Connection] = None

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    original_text TEXT NOT NULL,
    trust_score REAL NOT NULL,
    total_claims INTEGER NOT NULL DEFAULT 0,
    supported_count INTEGER NOT NULL DEFAULT 0,
    contradicted_count INTEGER NOT NULL DEFAULT 0,
    unverifiable_count INTEGER NOT NULL DEFAULT 0,
    latency_ms REAL NOT NULL DEFAULT 0,
    llm_prompt TEXT,
    report_json TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trust_score ON audit_logs(trust_score);
CREATE INDEX IF NOT EXISTS idx_created_at ON audit_logs(created_at);
"""


async def init_db():
    """Initialize the SQLite database and create tables."""
    global _db
    settings = get_settings()

    _db = await aiosqlite.connect(settings.audit_db_path)
    _db.row_factory = aiosqlite.Row
    await _db.executescript(CREATE_TABLE_SQL)
    await _db.commit()
    logger.info(f"Audit database initialized: {settings.audit_db_path}")


async def close_db():
    """Close the database connection."""
    global _db
    if _db is not None:
        await _db.close()
        _db = None
        logger.info("Audit database closed")


async def get_db() -> aiosqlite.Connection:
    """Get the database connection, initializing if needed."""
    global _db
    if _db is None:
        await init_db()
    return _db


async def save_audit(report: AuditReport) -> str:
    """
    Save an audit report to the database.
    
    Args:
        report: The AuditReport to persist.
        
    Returns:
        The report ID.
    """
    db = await get_db()

    report_json = report.model_dump_json()

    await db.execute(
        """
        INSERT OR REPLACE INTO audit_logs 
        (id, original_text, trust_score, total_claims, supported_count, 
         contradicted_count, unverifiable_count, latency_ms, llm_prompt, 
         report_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report.id,
            report.original_text[:500],  # Truncate for summary column
            report.trust_score,
            report.total_claims,
            report.supported_count,
            report.contradicted_count,
            report.unverifiable_count,
            report.latency_ms,
            report.llm_prompt,
            report_json,
            report.timestamp.isoformat(),
        )
    )
    await db.commit()
    logger.info(f"Saved audit report: {report.id}")
    return report.id


async def get_audit(audit_id: str) -> Optional[AuditReport]:
    """
    Retrieve a single audit report by ID.
    
    Args:
        audit_id: The unique report ID.
        
    Returns:
        AuditReport or None if not found.
    """
    db = await get_db()

    cursor = await db.execute(
        "SELECT report_json FROM audit_logs WHERE id = ?",
        (audit_id,)
    )
    row = await cursor.fetchone()

    if row is None:
        return None

    return AuditReport.model_validate_json(row[0])


async def get_audit_history(query: AuditHistoryQuery) -> AuditHistoryResponse:
    """
    Retrieve paginated audit history with filters.
    
    Args:
        query: Filter and pagination parameters.
        
    Returns:
        AuditHistoryResponse with results and total count.
    """
    db = await get_db()

    # Build WHERE clauses
    conditions = []
    params = []

    if query.min_trust_score is not None:
        conditions.append("trust_score >= ?")
        params.append(query.min_trust_score)

    if query.max_trust_score is not None:
        conditions.append("trust_score <= ?")
        params.append(query.max_trust_score)

    if query.start_date is not None:
        conditions.append("created_at >= ?")
        params.append(query.start_date.isoformat())

    if query.end_date is not None:
        conditions.append("created_at <= ?")
        params.append(query.end_date.isoformat())

    if query.has_contradictions is not None:
        if query.has_contradictions:
            conditions.append("contradicted_count > 0")
        else:
            conditions.append("contradicted_count = 0")

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Get total count
    count_cursor = await db.execute(
        f"SELECT COUNT(*) FROM audit_logs WHERE {where_clause}",
        params
    )
    total = (await count_cursor.fetchone())[0]

    # Get paginated results
    cursor = await db.execute(
        f"""
        SELECT report_json FROM audit_logs 
        WHERE {where_clause}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [query.limit, query.offset]
    )
    rows = await cursor.fetchall()

    audits = [AuditReport.model_validate_json(row[0]) for row in rows]

    return AuditHistoryResponse(
        audits=audits,
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


async def get_stats() -> Dict[str, Any]:
    """Get aggregate statistics from the audit log."""
    db = await get_db()

    cursor = await db.execute("""
        SELECT 
            COUNT(*) as total_audits,
            AVG(trust_score) as avg_trust_score,
            AVG(latency_ms) as avg_latency_ms,
            SUM(total_claims) as total_claims_processed,
            SUM(supported_count) as total_supported,
            SUM(contradicted_count) as total_contradicted,
            SUM(unverifiable_count) as total_unverifiable
        FROM audit_logs
    """)
    row = await cursor.fetchone()

    return {
        "total_audits": row[0] or 0,
        "avg_trust_score": round(row[1] or 0, 4),
        "avg_latency_ms": round(row[2] or 0, 2),
        "total_claims_processed": row[3] or 0,
        "total_supported": row[4] or 0,
        "total_contradicted": row[5] or 0,
        "total_unverifiable": row[6] or 0,
    }
