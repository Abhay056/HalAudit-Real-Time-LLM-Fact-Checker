"""
Tests for the NLI Scorer module.
"""

import pytest
import numpy as np
from app.core.nli_scorer import NLIScorer
from app.models.schemas import VerdictLabel


class TestNLIScorerUtils:
    """Test utility functions of the NLI scorer."""

    def test_softmax(self):
        """Test softmax normalization."""
        result = NLIScorer._softmax([1.0, 2.0, 3.0])
        assert abs(sum(result) - 1.0) < 1e-6
        assert result[2] > result[1] > result[0]

    def test_softmax_equal_values(self):
        """Test softmax with equal values."""
        result = NLIScorer._softmax([1.0, 1.0, 1.0])
        assert abs(result[0] - result[1]) < 1e-6
        assert abs(result[1] - result[2]) < 1e-6

    def test_interpret_scores_supported(self):
        """Test score interpretation when entailment is highest."""
        scorer = NLIScorer()
        # Index order: [contradiction, entailment, neutral]
        result = scorer._interpret_scores([0.1, 5.0, 0.5])
        assert result["label"] == VerdictLabel.SUPPORTED
        assert result["confidence"] > 0.9

    def test_interpret_scores_contradicted(self):
        """Test score interpretation when contradiction is highest."""
        scorer = NLIScorer()
        result = scorer._interpret_scores([5.0, 0.1, 0.5])
        assert result["label"] == VerdictLabel.CONTRADICTED
        assert result["confidence"] > 0.9

    def test_interpret_scores_unverifiable(self):
        """Test score interpretation when neutral is highest."""
        scorer = NLIScorer()
        result = scorer._interpret_scores([0.1, 0.5, 5.0])
        assert result["label"] == VerdictLabel.UNVERIFIABLE
        assert result["confidence"] > 0.9

    def test_interpret_numpy_scores(self):
        """Test that numpy arrays are handled correctly."""
        scorer = NLIScorer()
        scores = np.array([0.1, 5.0, 0.5])
        result = scorer._interpret_scores(scores)
        assert result["label"] == VerdictLabel.SUPPORTED


class TestNLIScorerEvidenceAggregation:
    """Test evidence aggregation logic."""

    @pytest.mark.asyncio
    async def test_no_evidence_returns_unverifiable(self):
        """Test that no evidence yields Unverifiable."""
        scorer = NLIScorer()
        result = await scorer.score_claim_with_evidence(
            "The sky is blue.",
            []
        )
        assert result["label"] == VerdictLabel.UNVERIFIABLE
        assert result["confidence"] == 1.0


class TestNLIScorerIntegration:
    """Integration tests that load the actual model."""

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_supported_claim(self):
        """Test a claim that should be supported by evidence."""
        scorer = NLIScorer()
        result = await scorer.score(
            "The capital of France is Paris.",
            "Paris is the capital of France."
        )
        assert result["label"] == VerdictLabel.SUPPORTED

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_contradicted_claim(self):
        """Test a claim that should be contradicted by evidence."""
        scorer = NLIScorer()
        result = await scorer.score(
            "Albert Einstein was born in Austria.",
            "Albert Einstein was born in Germany."
        )
        assert result["label"] == VerdictLabel.CONTRADICTED
