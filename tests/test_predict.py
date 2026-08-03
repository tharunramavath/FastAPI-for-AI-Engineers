"""
tests/test_predict.py — Testing FastAPI Endpoints
===================================================
CONCEPT: Testing with TestClient and pytest

FastAPI includes a TestClient (wraps httpx) that lets you test
your API without running a real server. This is the standard
pattern used in every production FastAPI codebase.

Run tests with:
  pytest tests/ -v

Why AI engineers need this:
  - You need to verify your inference endpoints before deploying
  - CI/CD pipelines run tests before every deployment
  - Prevents regressions when you update model versions
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# TestClient simulates an HTTP client — no real server needed
client = TestClient(app)

# Valid API key — matches what's in .env.example
VALID_KEY = "test-key-123"
HEADERS = {"X-API-Key": VALID_KEY}


# ─────────────────────────────────────────────────────────
# Health Check Tests (no auth)
# ─────────────────────────────────────────────────────────
class TestHealth:
    def test_health_returns_ok(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "models_loaded" in data
        assert len(data["models_loaded"]) > 0

    def test_health_no_auth_required(self):
        """Health endpoint should work WITHOUT an API key."""
        response = client.get("/health")  # no headers
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────
# Authentication Tests
# ─────────────────────────────────────────────────────────
class TestAuth:
    def test_predict_without_key_returns_401(self):
        response = client.post("/predict", json={"text": "hello"})
        assert response.status_code == 422  # missing required header

    def test_predict_with_wrong_key_returns_401(self):
        response = client.post(
            "/predict",
            json={"text": "hello"},
            headers={"X-API-Key": "wrong-key"},
        )
        assert response.status_code == 401

    def test_predict_with_valid_key_succeeds(self):
        response = client.post(
            "/predict",
            json={"text": "I love this!", "model": "sentiment"},
            headers=HEADERS,
        )
        assert response.status_code == 200


# ─────────────────────────────────────────────────────────
# Predict Endpoint Tests
# ─────────────────────────────────────────────────────────
class TestPredict:
    def test_sentiment_model_returns_valid_response(self):
        response = client.post(
            "/predict",
            json={"text": "This is amazing!", "model": "sentiment"},
            headers=HEADERS,
        )
        assert response.status_code == 200
        data = response.json()

        # Assert response structure matches PredictResponse schema
        assert "request_id" in data
        assert "output" in data
        assert "tokens_used" in data
        assert "latency_ms" in data
        assert data["model"] == "sentiment"
        assert data["confidence"] is not None  # sentiment includes confidence

    def test_llm_model_no_confidence_score(self):
        response = client.post(
            "/predict",
            json={"text": "Explain AI", "model": "llm"},
            headers=HEADERS,
        )
        data = response.json()
        assert data["confidence"] is None  # LLM doesn't return confidence

    def test_empty_text_returns_422(self):
        """Pydantic validation should reject empty text."""
        response = client.post(
            "/predict",
            json={"text": "", "model": "sentiment"},
            headers=HEADERS,
        )
        assert response.status_code == 422

    def test_invalid_model_returns_422(self):
        """Only allowed model names should be accepted."""
        response = client.post(
            "/predict",
            json={"text": "hello", "model": "gpt-99"},  # not in Literal
            headers=HEADERS,
        )
        assert response.status_code == 422

    def test_temperature_out_of_range_returns_422(self):
        response = client.post(
            "/predict",
            json={"text": "hello", "temperature": 5.0},  # max is 2.0
            headers=HEADERS,
        )
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────
# Models Endpoint Tests
# ─────────────────────────────────────────────────────────
class TestModels:
    def test_list_models_returns_all(self):
        response = client.get("/models", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert data["total"] > 0

    def test_get_specific_model(self):
        response = client.get("/models/sentiment", headers=HEADERS)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "sentiment"

    def test_get_nonexistent_model_returns_404(self):
        response = client.get("/models/fake-model", headers=HEADERS)
        assert response.status_code == 404
