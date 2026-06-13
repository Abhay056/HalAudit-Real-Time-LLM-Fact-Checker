"""
HalAudit Claim Extractor
Decomposes LLM responses into atomic, independently verifiable factual claims.
Uses OpenAI API with structured output, with fallback to sentence splitting.
"""

import json
import logging
import re
from typing import List, Optional
import os

from app.config import get_settings

logger = logging.getLogger(__name__)

# System prompt for claim extraction
CLAIM_EXTRACTION_PROMPT = """You are an expert fact-checker specializing in decomposing text into atomic factual claims.

Given a text passage, break it down into a list of atomic, self-contained factual claims.

Rules:
1. Each claim must be a SINGLE, independently verifiable statement of fact.
2. Each claim must be SELF-CONTAINED - no pronouns referring to other claims. Replace pronouns with the actual entity names.
3. Each claim must be MINIMAL - do not combine multiple facts into one claim.
4. Exclude opinions, subjective statements, and hedged language (e.g., "might", "could", "arguably").
5. Preserve numerical values, dates, and specific details exactly as stated.
6. If a sentence contains multiple facts, split them into separate claims.

Return ONLY a JSON object with a "claims" key containing an array of strings. No other text.

Example:
Input: "Albert Einstein, who was born in Germany in 1879, developed the theory of relativity and won the Nobel Prize in Physics in 1921."
Output: {"claims": ["Albert Einstein was born in Germany.", "Albert Einstein was born in 1879.", "Albert Einstein developed the theory of relativity.", "Albert Einstein won the Nobel Prize in Physics.", "Albert Einstein won the Nobel Prize in Physics in 1921."]}"""


class ClaimExtractor:
    """Extracts atomic factual claims from text using an LLM."""

    def __init__(self):
        self._client = None
        self.settings = get_settings()

    @property
    def client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.settings.openai_api_key,
                    base_url=os.environ.get("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
                )
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
                self._client = None
        return self._client

    async def extract_claims(self, text: str) -> List[str]:
        """
        Extract atomic factual claims from the given text.
        
        Args:
            text: The LLM response text to decompose.
            
        Returns:
            List of atomic claim strings.
        """
        # Try OpenAI-based extraction first
        if self.client and self.settings.openai_api_key:
            try:
                claims = await self._extract_with_llm(text)
                if claims:
                    logger.info(f"Extracted {len(claims)} claims via LLM")
                    return claims
            except Exception as e:
                logger.warning(f"LLM claim extraction failed, falling back: {e}")

        # Fallback: sentence-level splitting
        claims = self._extract_with_fallback(text)
        logger.info(f"Extracted {len(claims)} claims via fallback method")
        return claims

    async def _extract_with_llm(self, text: str) -> List[str]:
        """Extract claims using OpenAI API."""
        import asyncio

        # Run the synchronous OpenAI call in a thread pool
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {"role": "system", "content": CLAIM_EXTRACTION_PROMPT},
                    {"role": "user", "content": f"Decompose this text into atomic factual claims:\n\n{text}"}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )
        )

        content = response.choices[0].message.content.strip()
        parsed = json.loads(content)

        claims = parsed.get("claims", [])
        if not isinstance(claims, list):
            raise ValueError(f"Expected list of claims, got {type(claims)}")

        # Filter and clean claims
        cleaned = []
        for claim in claims:
            if isinstance(claim, str):
                claim = claim.strip()
                if len(claim) > 10:  # Skip trivially short claims
                    cleaned.append(claim)

        return cleaned

    def _extract_with_fallback(self, text: str) -> List[str]:
        """
        Fallback claim extraction using sentence splitting and filtering.
        Used when OpenAI is unavailable.
        """
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        claims = []
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # Skip very short sentences
            if len(sentence) < 15:
                continue

            # Skip questions
            if sentence.endswith('?'):
                continue

            # Skip clearly subjective statements
            subjective_markers = [
                'i think', 'i believe', 'in my opinion', 'arguably',
                'it seems', 'probably', 'maybe', 'perhaps', 'might',
                'could be', 'should be', 'it\'s possible'
            ]
            if any(marker in sentence.lower() for marker in subjective_markers):
                continue

            # Clean up
            sentence = sentence.strip('- •')
            if sentence and not sentence.endswith('.'):
                sentence += '.'

            claims.append(sentence)

        return claims


# Singleton instance
_extractor: Optional[ClaimExtractor] = None


def get_claim_extractor() -> ClaimExtractor:
    """Get the claim extractor singleton."""
    global _extractor
    if _extractor is None:
        _extractor = ClaimExtractor()
    return _extractor
