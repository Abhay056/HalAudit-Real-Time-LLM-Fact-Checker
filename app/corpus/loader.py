"""
HalAudit Corpus Loader
Handles loading and managing the document corpus for RAG retrieval.
"""

import logging
from typing import Optional

from app.core.rag_retriever import get_rag_retriever
from app.corpus.seed_data import get_seed_corpus

logger = logging.getLogger(__name__)


async def load_seed_corpus(force: bool = False) -> int:
    """
    Load the seed corpus into ChromaDB if it hasn't been loaded yet.
    
    Args:
        force: If True, reload even if corpus already has data.
        
    Returns:
        Number of documents in the corpus after loading.
    """
    retriever = get_rag_retriever()
    current_size = retriever.get_corpus_size()

    if current_size > 0 and not force:
        logger.info(f"Corpus already loaded with {current_size} documents. Skipping seed data.")
        return current_size

    if force and current_size > 0:
        logger.info("Force reloading seed corpus...")
        await retriever.clear_corpus()

    texts, metadata = get_seed_corpus()
    ingested = await retriever.ingest(texts, metadata, source="seed")

    total = retriever.get_corpus_size()
    logger.info(f"Seed corpus loaded: {ingested} documents ingested. Total: {total}")
    return total


async def get_corpus_stats() -> dict:
    """Get statistics about the current corpus."""
    retriever = get_rag_retriever()
    return {
        "total_documents": retriever.get_corpus_size(),
    }
