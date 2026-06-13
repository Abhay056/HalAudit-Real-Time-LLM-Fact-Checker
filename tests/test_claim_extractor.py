"""
Tests for the Claim Extractor module.
"""

import pytest
import asyncio
from app.core.claim_extractor import ClaimExtractor


class TestClaimExtractorFallback:
    """Test the fallback (non-LLM) claim extraction."""

    def setup_method(self):
        self.extractor = ClaimExtractor()

    def test_sentence_splitting(self):
        """Test that text is correctly split into sentences."""
        text = "The sky is very blue today. Water is definitely wet. Fire is extremely hot."
        claims = self.extractor._extract_with_fallback(text)
        assert len(claims) == 3

    def test_filters_short_sentences(self):
        """Test that very short sentences are filtered out."""
        text = "Hi. This is a valid claim about the world. Ok."
        claims = self.extractor._extract_with_fallback(text)
        assert len(claims) == 1
        assert "valid claim" in claims[0]

    def test_filters_questions(self):
        """Test that questions are filtered out."""
        text = "Is the sky blue? The sky is blue."
        claims = self.extractor._extract_with_fallback(text)
        assert len(claims) == 1
        assert claims[0].startswith("The sky is blue")

    def test_filters_subjective_statements(self):
        """Test that subjective statements are filtered."""
        text = "I think cats are great. Cats are mammals. Perhaps dogs are better."
        claims = self.extractor._extract_with_fallback(text)
        assert len(claims) == 1
        assert "mammals" in claims[0]

    def test_empty_input(self):
        """Test that empty input returns no claims."""
        claims = self.extractor._extract_with_fallback("")
        assert len(claims) == 0

    @pytest.mark.asyncio
    async def test_async_extract_claims_fallback(self):
        """Test the async extract_claims falls back gracefully without API key."""
        extractor = ClaimExtractor()
        extractor._client = None  # Force no client

        text = "The Earth orbits the Sun. Water boils at 100 degrees Celsius."
        claims = await extractor.extract_claims(text)
        assert len(claims) >= 2


class TestClaimExtractorIntegration:
    """Integration tests that require OpenAI API key."""

    @pytest.mark.skipif(
        True,  # Set to False and provide API key to run
        reason="Requires OpenAI API key"
    )
    @pytest.mark.asyncio
    async def test_llm_extraction(self):
        """Test claim extraction via OpenAI API."""
        extractor = ClaimExtractor()
        text = (
            "Albert Einstein was born in Germany in 1879. "
            "He developed the theory of relativity and won the Nobel Prize "
            "in Physics in 1921 for the photoelectric effect."
        )
        claims = await extractor.extract_claims(text)
        assert len(claims) >= 3
        # Should have decomposed into atomic facts
        assert any("Germany" in c for c in claims)
        assert any("1879" in c for c in claims)
