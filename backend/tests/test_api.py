"""End-to-end smoke tests using in-memory stores (no AWS)."""
import asyncio
import os
import sys
import time

import pytest

# Force local dev mode
os.environ["USE_LOCAL_STORE"] = "true"
os.environ["EMBEDDING_PROVIDER"] = "local"
os.environ["LOCAL_STORAGE_PATH"] = "/tmp/adaptive-rag-test"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from backend.api.main import app
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_ingest_and_poll(client):
    content = b"The adaptive RAG platform supports multiple file types including PDF, CSV, and JSON."
    resp = client.post(
        "/ingest",
        files={"file": ("test.txt", content, "text/plain")},
    )
    assert resp.status_code == 202
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"

    job_id = data["job_id"]

    # Poll until READY or timeout
    deadline = time.time() + 30
    status = "PENDING"
    while time.time() < deadline:
        poll = client.get(f"/jobs/{job_id}")
        assert poll.status_code == 200
        status = poll.json()["status"]
        if status in ("READY", "FAILED"):
            break
        time.sleep(0.5)

    assert status == "READY", f"Job did not complete: {status}"
    poll_data = client.get(f"/jobs/{job_id}").json()
    assert poll_data["record_count"] > 0


def test_query_returns_valid_shape(client):
    resp = client.post("/query", json={"query": "What is the adaptive RAG platform?", "top_k": 3})
    assert resp.status_code == 200
    data = resp.json()
    assert "answer" in data
    assert "sources" in data
    assert "ui_schema" in data
    assert "cache_hit" in data

    ui = data["ui_schema"]
    assert ui["version"] == "1.0"
    assert "layout" in ui
    assert "data_bindings" in ui


def test_query_cache_hit(client):
    query = "What file types are supported?"
    resp1 = client.post("/query", json={"query": query})
    assert resp1.status_code == 200
    assert resp1.json()["cache_hit"] is False

    resp2 = client.post("/query", json={"query": query})
    assert resp2.status_code == 200
    assert resp2.json()["cache_hit"] is True


def test_job_not_found(client):
    resp = client.get("/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_ingest_json(client):
    resp = client.post(
        "/ingest/json",
        json={"data": [{"product": "Widget", "price": 9.99}], "source_label": "test-catalog"},
    )
    assert resp.status_code == 202
    assert "job_id" in resp.json()


def test_ui_schema_endpoint(client):
    resp = client.post(
        "/ui-schema",
        json={"data": {"metric": 42, "label": "count"}, "intent": "show metric"},
    )
    assert resp.status_code == 200
    assert "ui_schema" in resp.json()
