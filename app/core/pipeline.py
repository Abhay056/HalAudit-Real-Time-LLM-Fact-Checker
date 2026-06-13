"""
HalAudit Pipeline Orchestrator
Orchestrates the full audit: claim extraction → RAG retrieval → NLI scoring.
"""

import asyncio
import logging
import time
from typing import Optional

from app.config import get_settings
from app.core.claim_extractor import get_claim_extractor
from app.core.rag_retriever import get_rag_retriever
from app.core.nli_scorer import get_nli_scorer
from app.models.schemas import (
    AuditReport, ClaimResult, EvidenceChunk,
    AuditOptions, VerdictLabel
)

logger = logging.getLogger(__name__)


class AuditPipeline:
    """Orchestrates the complete hallucination audit pipeline."""

    def __init__(self):
        self.settings = get_settings()
        self.claim_extractor = get_claim_extractor()
        self.rag_retriever = get_rag_retriever()
        self.nli_scorer = get_nli_scorer()

    async def audit(
        self,
        text: str,
        options: Optional[AuditOptions] = None,
        llm_prompt: Optional[str] = None
    ) -> AuditReport:
        """
        Run the full audit pipeline on a text.
        
        Args:
            text: The LLM response text to audit.
            options: Optional configuration overrides.
            llm_prompt: Original prompt if using generate-and-audit.
            
        Returns:
            Complete AuditReport with per-claim verdicts and trust score.
        """
        total_start = time.time()
        latency_breakdown = {}

        # Override defaults with options if provided
        top_k = options.top_k if options else self.settings.rag_top_k
        supported_threshold = (
            options.supported_threshold
            if options and options.supported_threshold is not None
            else self.settings.supported_threshold
        )
        contradicted_threshold = (
            options.contradicted_threshold
            if options and options.contradicted_threshold is not None
            else self.settings.contradicted_threshold
        )

        # Temporarily override thresholds on the scorer
        original_supported = self.settings.supported_threshold
        original_contradicted = self.settings.contradicted_threshold
        self.settings.supported_threshold = supported_threshold
        self.settings.contradicted_threshold = contradicted_threshold

        try:
            # --- Step 1: Claim Extraction ---
            step_start = time.time()
            claims = await self.claim_extractor.extract_claims(text)
            latency_breakdown["claim_extraction_ms"] = round(
                (time.time() - step_start) * 1000, 2
            )
            logger.info(f"Step 1: Extracted {len(claims)} claims")

            if not claims:
                return AuditReport(
                    original_text=text,
                    claims=[],
                    trust_score=0.0,
                    latency_ms=round((time.time() - total_start) * 1000, 2),
                    latency_breakdown=latency_breakdown,
                    llm_prompt=llm_prompt,
                )

            # --- Step 2: RAG Retrieval (parallel for all claims) ---
            step_start = time.time()
            retrieval_tasks = [
                self.rag_retriever.retrieve(claim, top_k=top_k)
                for claim in claims
            ]
            all_evidence = await asyncio.gather(*retrieval_tasks)
            latency_breakdown["rag_retrieval_ms"] = round(
                (time.time() - step_start) * 1000, 2
            )
            logger.info(f"Step 2: Retrieved evidence for {len(claims)} claims")

            # --- Step 3: NLI Scoring (parallel for all claims) ---
            step_start = time.time()
            scoring_tasks = [
                self.nli_scorer.score_claim_with_evidence(claim, evidence)
                for claim, evidence in zip(claims, all_evidence)
            ]
            all_verdicts = await asyncio.gather(*scoring_tasks)
            latency_breakdown["nli_scoring_ms"] = round(
                (time.time() - step_start) * 1000, 2
            )
            logger.info(f"Step 3: Scored {len(claims)} claims")

            # --- Step 4: Assemble Report ---
            claim_results = []
            for claim, evidence_chunks, verdict in zip(claims, all_evidence, all_verdicts):
                evidence_models = [
                    EvidenceChunk(
                        text=chunk["text"],
                        source=chunk.get("source", "corpus"),
                        relevance_score=chunk.get("relevance_score", 0.0)
                    )
                    for chunk in evidence_chunks
                ]

                claim_results.append(ClaimResult(
                    claim=claim,
                    label=verdict["label"],
                    confidence=verdict["confidence"],
                    evidence=evidence_models,
                    reasoning=verdict.get("reasoning"),
                ))

            total_latency = round((time.time() - total_start) * 1000, 2)

            report = AuditReport(
                original_text=text,
                claims=claim_results,
                latency_ms=total_latency,
                latency_breakdown=latency_breakdown,
                llm_prompt=llm_prompt,
            )
            report.compute_trust_score()

            logger.info(
                f"Audit complete: {report.total_claims} claims, "
                f"trust_score={report.trust_score:.2%}, "
                f"latency={total_latency}ms"
            )

            return report

        finally:
            # Restore original thresholds
            self.settings.supported_threshold = original_supported
            self.settings.contradicted_threshold = original_contradicted

    async def generate_and_audit(
        self,
        prompt: str,
        options: Optional[AuditOptions] = None
    ) -> AuditReport:
        """
        Generate an LLM response from a prompt, then audit it.
        
        Args:
            prompt: The user prompt to send to the LLM.
            options: Optional audit configuration.
            
        Returns:
            AuditReport including the generated response.
        """
        # Generate LLM response
        extractor = get_claim_extractor()
        if not extractor.client:
            raise ValueError(
                "OpenAI API key required for generate-and-audit. "
                "Set OPENAI_API_KEY in your environment."
            )

        import asyncio

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: extractor.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
            )
        )

        llm_response = response.choices[0].message.content.strip()
        logger.info(f"Generated LLM response: {len(llm_response)} chars")

        # Now audit the response
        return await self.audit(llm_response, options=options, llm_prompt=prompt)


# Singleton instance
_pipeline: Optional[AuditPipeline] = None


def get_audit_pipeline() -> AuditPipeline:
    """Get the audit pipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = AuditPipeline()
    return _pipeline
