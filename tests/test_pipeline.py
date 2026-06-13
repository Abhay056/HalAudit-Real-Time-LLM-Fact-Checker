"""
Tests for the full audit pipeline.
"""

import pytest
from app.models.schemas import AuditReport, ClaimResult, VerdictLabel, EvidenceChunk


class TestAuditReport:
    """Test AuditReport model logic."""

    def test_trust_score_all_supported(self):
        """Test trust score when all claims are supported."""
        report = AuditReport(
            original_text="Test text",
            claims=[
                ClaimResult(claim="Claim 1", label=VerdictLabel.SUPPORTED, confidence=0.9),
                ClaimResult(claim="Claim 2", label=VerdictLabel.SUPPORTED, confidence=0.8),
            ]
        )
        report.compute_trust_score()
        assert report.trust_score == 1.0
        assert report.supported_count == 2

    def test_trust_score_all_contradicted(self):
        """Test trust score when all claims are contradicted."""
        report = AuditReport(
            original_text="Test text",
            claims=[
                ClaimResult(claim="Claim 1", label=VerdictLabel.CONTRADICTED, confidence=0.9),
                ClaimResult(claim="Claim 2", label=VerdictLabel.CONTRADICTED, confidence=0.8),
            ]
        )
        report.compute_trust_score()
        assert report.trust_score == 0.0
        assert report.contradicted_count == 2

    def test_trust_score_mixed(self):
        """Test trust score with mixed verdicts."""
        report = AuditReport(
            original_text="Test text",
            claims=[
                ClaimResult(claim="Claim 1", label=VerdictLabel.SUPPORTED, confidence=0.9),
                ClaimResult(claim="Claim 2", label=VerdictLabel.CONTRADICTED, confidence=0.8),
                ClaimResult(claim="Claim 3", label=VerdictLabel.UNVERIFIABLE, confidence=0.7),
            ]
        )
        report.compute_trust_score()
        # (1.0 + 0.0 + 0.5) / 3 = 0.5
        assert report.trust_score == 0.5

    def test_trust_score_empty_claims(self):
        """Test trust score with no claims."""
        report = AuditReport(original_text="Test text", claims=[])
        report.compute_trust_score()
        assert report.trust_score == 0.0

    def test_evidence_chunk_model(self):
        """Test EvidenceChunk model."""
        chunk = EvidenceChunk(
            text="Some evidence",
            source="Wikipedia",
            relevance_score=0.85
        )
        assert chunk.text == "Some evidence"
        assert chunk.relevance_score == 0.85

    def test_report_serialization(self):
        """Test that AuditReport can be serialized and deserialized."""
        report = AuditReport(
            original_text="Test text",
            claims=[
                ClaimResult(
                    claim="Test claim",
                    label=VerdictLabel.SUPPORTED,
                    confidence=0.9,
                    evidence=[
                        EvidenceChunk(text="Evidence", source="test", relevance_score=0.8)
                    ],
                    reasoning="Supported by evidence",
                )
            ]
        )
        report.compute_trust_score()

        # Serialize
        json_str = report.model_dump_json()
        assert "Test claim" in json_str

        # Deserialize
        restored = AuditReport.model_validate_json(json_str)
        assert restored.trust_score == report.trust_score
        assert len(restored.claims) == 1
        assert restored.claims[0].label == VerdictLabel.SUPPORTED
