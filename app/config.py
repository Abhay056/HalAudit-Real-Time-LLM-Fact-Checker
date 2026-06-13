"""
HalAudit Configuration Module
Centralized settings using Pydantic BaseSettings with .env support.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # --- OpenAI Configuration ---
    openai_api_key: str = Field(default="", description="API key for claim extraction (OpenAI or Groq)")
    openai_model: str = Field(default="llama-3.3-70b-versatile", description="Model for claim extraction")

    # --- Redis Configuration ---
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")

    # --- ML Model Configuration ---
    nli_model_name: str = Field(
        default="cross-encoder/nli-deberta-v3-base",
        description="HuggingFace NLI cross-encoder model"
    )
    embedding_model_name: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence-transformers embedding model"
    )

    # --- ChromaDB Configuration ---
    chroma_persist_dir: str = Field(
        default="./chroma_data",
        description="Directory for ChromaDB persistence"
    )

    # --- Confidence Thresholds ---
    supported_threshold: float = Field(
        default=0.6,
        ge=0.0, le=1.0,
        description="Minimum confidence to label a claim as Supported"
    )
    contradicted_threshold: float = Field(
        default=0.6,
        ge=0.0, le=1.0,
        description="Minimum confidence to label a claim as Contradicted"
    )

    # --- Rate Limiting ---
    rate_limit_per_minute: int = Field(
        default=30,
        description="Maximum API requests per minute per client"
    )

    # --- Server Configuration ---
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    # --- Database ---
    audit_db_path: str = Field(
        default="./audit_logs.db",
        description="SQLite database path for audit logs"
    )

    # --- RAG Configuration ---
    rag_top_k: int = Field(default=3, description="Number of evidence chunks to retrieve per claim")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the application settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
