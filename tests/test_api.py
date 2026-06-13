"""
Tests for the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check(self, client):
        """Test that health check returns 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "components" in data


class TestAuditEndpoint:
    """Test the audit endpoint."""

    def test_audit_requires_text(self, client):
        """Test that audit requires text field."""
        response = client.post("/api/v1/audit", json={})
        assert response.status_code == 422

    def test_audit_rejects_short_text(self, client):
        """Test that very short text is rejected."""
        response = client.post("/api/v1/audit", json={"text": "Short"})
        assert response.status_code == 422

    def test_audit_accepts_valid_text(self, client):
        """Test that valid text is accepted and audited."""
        response = client.post(
            "/api/v1/audit",
            json={
                "text": "The speed of light is approximately 300,000 kilometers per second. Water boils at 100 degrees Celsius."
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "trust_score" in data
        assert "claims" in data
        assert isinstance(data["claims"], list)


class TestCorpusEndpoint:
    """Test corpus management endpoints."""

    def test_ingest_corpus(self, client):
        """Test corpus ingestion."""
        response = client.post(
            "/api/v1/corpus/ingest",
            json={
                "texts": ["The sun is a star.", "Water is H2O."],
                "source": "test"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ingested_count"] == 2


class TestHistoryEndpoint:
    """Test audit history endpoint."""

    def test_get_history(self, client):
        """Test that history endpoint returns paginated results."""
        response = client.get("/api/v1/audit/history")
        assert response.status_code == 200
        data = response.json()
        assert "audits" in data
        assert "total" in data
        assert "limit" in data


class TestStatsEndpoint:
    """Test stats endpoint."""

    def test_get_stats(self, client):
        """Test that stats endpoint returns aggregate data."""
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_audits" in data
