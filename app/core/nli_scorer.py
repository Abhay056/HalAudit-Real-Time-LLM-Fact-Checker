"""
HalAudit NLI Scorer
Uses a cross-encoder NLI model to classify claim-evidence pairs as
Supported, Contradicted, or Unverifiable.
"""

import logging
from typing import List, Tuple, Dict, Optional
import numpy as np

from app.config import get_settings
from app.models.schemas import VerdictLabel

logger = logging.getLogger(__name__)

# NLI model label mapping (DeBERTa NLI output order)
# Index 0: contradiction, Index 1: entailment, Index 2: neutral
NLI_LABELS = {
    0: VerdictLabel.CONTRADICTED,
    1: VerdictLabel.SUPPORTED,
    2: VerdictLabel.UNVERIFIABLE,
}


class NLIScorer:
    """Scores claim-evidence pairs using a cross-encoder NLI model."""

    def __init__(self):
        self.settings = get_settings()
        self._model = None

    @property
    def model(self):
        """Lazy-load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(
                    self.settings.nli_model_name,
                    max_length=512,
                )
                logger.info(f"Loaded NLI model: {self.settings.nli_model_name}")
            except Exception as e:
                logger.error(f"Failed to load NLI model: {e}")
                raise
        return self._model

    async def score(
        self,
        claim: str,
        evidence: str
    ) -> Dict:
        """
        Score a single claim-evidence pair.
        
        Args:
            claim: The factual claim to verify.
            evidence: The evidence text to check against.
            
        Returns:
            Dict with keys: label (VerdictLabel), confidence (float),
            scores (dict of all label scores)
        """
        import asyncio

        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(
            None,
            lambda: self.model.predict([(claim, evidence)])
        )

        return self._interpret_scores(scores[0])

    async def score_batch(
        self,
        pairs: List[Tuple[str, str]]
    ) -> List[Dict]:
        """
        Score multiple claim-evidence pairs in batch.
        
        Args:
            pairs: List of (claim, evidence) tuples.
            
        Returns:
            List of result dicts, one per pair.
        """
        if not pairs:
            return []

        import asyncio

        loop = asyncio.get_event_loop()
        all_scores = await loop.run_in_executor(
            None,
            lambda: self.model.predict(pairs)
        )

        results = []
        for scores in all_scores:
            results.append(self._interpret_scores(scores))

        return results

    async def score_claim_with_evidence(
        self,
        claim: str,
        evidence_chunks: List[Dict]
    ) -> Dict:
        """
        Score a claim against multiple evidence chunks and return the best verdict.
        
        The verdict is determined by the evidence chunk that gives the highest
        confidence for either Supported or Contradicted. If no evidence provides
        high confidence, the claim is labeled Unverifiable.
        
        Args:
            claim: The factual claim.
            evidence_chunks: List of evidence dicts with 'text' key.
            
        Returns:
            Dict with: label, confidence, best_evidence_index, all_scores
        """
        if not evidence_chunks:
            return {
                "label": VerdictLabel.UNVERIFIABLE,
                "confidence": 1.0,
                "reasoning": "No evidence found in the corpus for this claim.",
                "all_scores": []
            }

        # Create pairs for batch scoring
        pairs = [(claim, chunk["text"]) for chunk in evidence_chunks]
        all_results = await self.score_batch(pairs)

        # Find the best verdict across all evidence chunks
        best_supported = {"confidence": 0.0, "index": -1}
        best_contradicted = {"confidence": 0.0, "index": -1}

        for i, result in enumerate(all_results):
            if result["label"] == VerdictLabel.SUPPORTED and result["confidence"] > best_supported["confidence"]:
                best_supported = {"confidence": result["confidence"], "index": i}
            elif result["label"] == VerdictLabel.CONTRADICTED and result["confidence"] > best_contradicted["confidence"]:
                best_contradicted = {"confidence": result["confidence"], "index": i}

        # Decision logic with configurable thresholds
        if (best_contradicted["confidence"] >= self.settings.contradicted_threshold and
                best_contradicted["confidence"] > best_supported["confidence"]):
            label = VerdictLabel.CONTRADICTED
            confidence = best_contradicted["confidence"]
            best_idx = best_contradicted["index"]
            reasoning = f"Evidence contradicts this claim (confidence: {confidence:.2%})."
        elif best_supported["confidence"] >= self.settings.supported_threshold:
            label = VerdictLabel.SUPPORTED
            confidence = best_supported["confidence"]
            best_idx = best_supported["index"]
            reasoning = f"Evidence supports this claim (confidence: {confidence:.2%})."
        else:
            label = VerdictLabel.UNVERIFIABLE
            confidence = max(
                r["scores"].get(VerdictLabel.UNVERIFIABLE, 0.0) for r in all_results
            ) if all_results else 1.0
            best_idx = 0
            reasoning = "Insufficient evidence to verify or refute this claim."

        return {
            "label": label,
            "confidence": round(confidence, 4),
            "reasoning": reasoning,
            "best_evidence_index": best_idx,
            "all_scores": [
                {
                    "evidence_index": i,
                    "scores": r["scores"]
                }
                for i, r in enumerate(all_results)
            ]
        }

    def _interpret_scores(self, scores) -> Dict:
        """
        Interpret raw model scores into a verdict.
        
        Args:
            scores: Raw model output (numpy array or list of 3 values).
            
        Returns:
            Dict with label, confidence, and per-label scores.
        """
        if isinstance(scores, np.ndarray):
            scores = scores.tolist()
        elif not isinstance(scores, list):
            scores = list(scores)

        # Apply softmax to get probabilities
        probs = self._softmax(scores)

        # Map to labels
        label_scores = {}
        for idx, label in NLI_LABELS.items():
            label_scores[label] = round(probs[idx], 4)

        # Get the highest scoring label
        max_idx = int(np.argmax(probs))
        label = NLI_LABELS[max_idx]
        confidence = label_scores[label]

        return {
            "label": label,
            "confidence": confidence,
            "scores": label_scores,
        }

    @staticmethod
    def _softmax(x: List[float]) -> List[float]:
        """Compute softmax probabilities."""
        arr = np.array(x, dtype=np.float64)
        exp_x = np.exp(arr - np.max(arr))
        return (exp_x / exp_x.sum()).tolist()


# Singleton instance
_scorer: Optional[NLIScorer] = None


def get_nli_scorer() -> NLIScorer:
    """Get the NLI scorer singleton."""
    global _scorer
    if _scorer is None:
        _scorer = NLIScorer()
    return _scorer
