"""
HalAudit Pydantic Schemas
Request/Response models for the API and internal pipeline.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


class VerdictLabel(str, Enum):
    """Possible verdict labels for a claim."""
    SUPPORTED = "Supported"
    CONTRADICTED = "Contradicted"
    UNVERIFIABLE = "Unverifiable"


class AuditOptions(BaseModel):
    """Configurable options for an audit run."""
    top_k: int = Field(default=3, ge=1, le=10, description="Number of evidence chunks per claim")
    supported_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    contradicted_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class AuditRequest(BaseModel):
    """Request body for the audit endpoint."""
    text: str = Field(..., min_length=10, max_length=10000, description="LLM response text to audit")
    options: Optional[AuditOptions] = Field(default=None, description="Optional audit configuration")

    model_config = {"json_schema_extra": {
        "examples": [{
            "text": "The Great Wall of China is visible from space. It was built in the 3rd century BC by Emperor Qin Shi Huang.",
            "options": {"top_k": 3}
        }]
    }}


class GenerateAndAuditRequest(BaseModel):
    """Request body for generate-and-audit endpoint."""
    prompt: str = Field(..., min_length=5, max_length=5000, description="Prompt to send to the LLM")
    options: Optional[AuditOptions] = Field(default=None)


class EvidenceChunk(BaseModel):
    """A single piece of retrieved evidence."""
    text: str = Field(..., description="The evidence text")
    source: str = Field(default="corpus", description="Source identifier")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Semantic similarity score")


class ClaimResult(BaseModel):
    """Result for a single audited claim."""
    claim: str = Field(..., description="The atomic factual claim")
    label: VerdictLabel = Field(..., description="Verdict: Supported, Contradicted, or Unverifiable")
    confidence: float = Field(..., ge=0.0, le=1.0, description="NLI model confidence score")
    evidence: List[EvidenceChunk] = Field(default_factory=list, description="Retrieved evidence chunks")
    reasoning: Optional[str] = Field(default=None, description="Brief explanation of the verdict")


class AuditReport(BaseModel):
    """Complete audit report for an LLM response."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique audit report ID")
    original_text: str = Field(..., description="The original LLM response text")
    claims: List[ClaimResult] = Field(default_factory=list, description="Per-claim audit results")
    trust_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Aggregate trust score (0-1)")
    total_claims: int = Field(default=0, description="Total number of claims extracted")
    supported_count: int = Field(default=0)
    contradicted_count: int = Field(default=0)
    unverifiable_count: int = Field(default=0)
    latency_ms: float = Field(default=0.0, description="Total pipeline latency in milliseconds")
    latency_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="Per-component latency breakdown in ms"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    llm_prompt: Optional[str] = Field(default=None, description="Original prompt if generate-and-audit was used")

    def compute_trust_score(self) -> None:
        """Calculate aggregate trust score from claim results."""
        if not self.claims:
            self.trust_score = 0.0
            return

        self.total_claims = len(self.claims)
        self.supported_count = sum(1 for c in self.claims if c.label == VerdictLabel.SUPPORTED)
        self.contradicted_count = sum(1 for c in self.claims if c.label == VerdictLabel.CONTRADICTED)
        self.unverifiable_count = sum(1 for c in self.claims if c.label == VerdictLabel.UNVERIFIABLE)

        # Weighted scoring: supported=1.0, unverifiable=0.5, contradicted=0.0
        weighted_sum = (
            self.supported_count * 1.0 +
            self.unverifiable_count * 0.5 +
            self.contradicted_count * 0.0
        )
        self.trust_score = round(weighted_sum / self.total_claims, 4)


class AuditStatusResponse(BaseModel):
    """Response for async audit status check."""
    job_id: str
    status: str = Field(..., description="pending | processing | completed | failed")
    result: Optional[AuditReport] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


class CorpusIngestRequest(BaseModel):
    """Request to ingest documents into the corpus."""
    texts: List[str] = Field(..., min_length=1, description="List of text chunks to ingest")
    metadata: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Optional metadata for each text chunk"
    )
    source: str = Field(default="manual", description="Source identifier for these documents")


class CorpusIngestResponse(BaseModel):
    """Response after corpus ingestion."""
    ingested_count: int
    total_corpus_size: int
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    components: Dict[str, str] = Field(default_factory=dict)


class AuditHistoryQuery(BaseModel):
    """Query parameters for audit history."""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    min_trust_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_trust_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    has_contradictions: Optional[bool] = None


class AuditHistoryResponse(BaseModel):
    """Paginated audit history response."""
    audits: List[AuditReport]
    total: int
    limit: int
    offset: int
