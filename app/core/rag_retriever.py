"""
HalAudit RAG Retriever
Retrieves evidence chunks from a trusted corpus using ChromaDB and sentence-transformers.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
import uuid

from app.config import get_settings

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retrieves evidence from a ChromaDB vector store using semantic search."""

    def __init__(self):
        self.settings = get_settings()
        self._chroma_client = None
        self._collection = None
        self._embedding_fn = None

    def _get_embedding_function(self):
        """Lazy-load the embedding function."""
        if self._embedding_fn is None:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            self._embedding_fn = SentenceTransformerEmbeddingFunction(
                model_name=self.settings.embedding_model_name
            )
            logger.info(f"Loaded embedding model: {self.settings.embedding_model_name}")
        return self._embedding_fn

    def _get_collection(self):
        """Lazy-load the ChromaDB collection."""
        if self._collection is None:
            import chromadb

            self._chroma_client = chromadb.PersistentClient(
                path=self.settings.chroma_persist_dir
            )

            self._collection = self._chroma_client.get_or_create_collection(
                name="halaudit_corpus",
                embedding_function=self._get_embedding_function(),
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(
                f"ChromaDB collection ready. Documents: {self._collection.count()}"
            )
        return self._collection

    async def retrieve(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the most relevant evidence chunks for a given query/claim.
        
        Args:
            query: The claim text to search for evidence.
            top_k: Number of results to return.
            
        Returns:
            List of evidence dicts with keys: text, source, relevance_score
        """
        import asyncio

        collection = self._get_collection()

        if collection.count() == 0:
            logger.warning("Corpus is empty. No evidence can be retrieved.")
            return []

        # Run ChromaDB query in thread pool (it's synchronous)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: collection.query(
                query_texts=[query],
                n_results=min(top_k, collection.count()),
                include=["documents", "metadatas", "distances"]
            )
        )

        evidence_chunks = []
        if results and results["documents"] and results["documents"][0]:
            documents = results["documents"][0]
            distances = results["distances"][0] if results["distances"] else [0.0] * len(documents)
            metadatas = results["metadatas"][0] if results["metadatas"] else [{}] * len(documents)

            for doc, dist, meta in zip(documents, distances, metadatas):
                # ChromaDB cosine distance: 0 = identical, 2 = opposite
                # Convert to similarity score: 1 - (distance / 2)
                relevance_score = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

                evidence_chunks.append({
                    "text": doc,
                    "source": meta.get("source", "corpus"),
                    "relevance_score": round(relevance_score, 4)
                })

        return evidence_chunks

    async def ingest(
        self,
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
        source: str = "manual"
    ) -> int:
        """
        Ingest new documents into the corpus.
        
        Args:
            texts: List of text chunks to add.
            metadata: Optional metadata for each chunk.
            source: Source identifier.
            
        Returns:
            Number of documents ingested.
        """
        import asyncio

        collection = self._get_collection()

        # Generate unique IDs
        ids = [str(uuid.uuid4()) for _ in texts]

        # Prepare metadata
        if metadata is None:
            metadata = [{"source": source} for _ in texts]
        else:
            # Ensure source is in each metadata dict
            for meta in metadata:
                if "source" not in meta:
                    meta["source"] = source

        # Add to collection in thread pool
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: collection.add(
                documents=texts,
                metadatas=metadata,
                ids=ids
            )
        )

        logger.info(f"Ingested {len(texts)} documents. Total: {collection.count()}")
        return len(texts)

    def get_corpus_size(self) -> int:
        """Get the total number of documents in the corpus."""
        return self._get_collection().count()

    async def clear_corpus(self) -> None:
        """Clear all documents from the corpus."""
        import chromadb

        if self._chroma_client:
            self._chroma_client.delete_collection("halaudit_corpus")
            self._collection = None
            logger.info("Corpus cleared")


# Singleton instance
_retriever: Optional[RAGRetriever] = None


def get_rag_retriever() -> RAGRetriever:
    """Get the RAG retriever singleton."""
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
