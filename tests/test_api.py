"""Integration tests for the FastAPI application.

Uses FastAPI TestClient for in-process requests against the real app.
Patches config paths at module level for all dependent modules.
"""
import sys, os, json, shutil, tempfile
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import backend.config
import backend.loader
import backend.chunker
import backend.indexer
import backend.embedder
import backend.retriever
import backend.history
import backend.main

from backend.main import app


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure no cross-test pollution from caches."""
    from backend.retriever import clear_kb_cache
    clear_kb_cache()
    yield


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_dir(tmp_path):
    """Create temp knowledge_bases dir with one KB."""
    kb_root = tmp_path / "knowledge_bases"
    kb_path = kb_root / "test_dongba"
    kb_path.mkdir(parents=True, exist_ok=True)
    (kb_path / "东巴文化.txt").write_text(
        "东巴文化是纳西族的传统文化。东巴文字是一种象形文字。", encoding="utf-8"
    )

    modules_using_kb_dir = [
        backend.config, backend.loader, backend.chunker,
        backend.indexer, backend.embedder,
        backend.main,
    ]
    patchers = [
        patch.object(m, "KNOWLEDGE_BASES_DIR", kb_root)
        for m in modules_using_kb_dir
    ]
    for p in patchers:
        p.start()
    yield kb_root
    for p in patchers:
        p.stop()


# ── Health ──


def test_health_check(client, temp_dir):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.1.0"


# ── KB List ──


def test_kb_list(client, temp_dir):
    resp = client.get("/api/kb/list")
    assert resp.status_code == 200
    data = resp.json()
    assert "knowledge_bases" in data
    kb_names = [kb["name"] for kb in data["knowledge_bases"]]
    assert "test_dongba" in kb_names


# ── KB Info ──


def test_kb_info(client, temp_dir):
    resp = client.get("/api/kb/test_dongba/info")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "test_dongba"
    assert data["document_count"] >= 1


def test_kb_info_not_found(client, temp_dir):
    resp = client.get("/api/kb/nonexistent/info")
    assert resp.status_code == 404


# ── Create / Delete KB ──


def test_create_and_delete_kb(client, temp_dir):
    resp = client.post("/api/kb/create", json={"name": "new_test_kb"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Duplicate should 409
    resp = client.post("/api/kb/create", json={"name": "new_test_kb"})
    assert resp.status_code == 409

    # Delete
    resp = client.delete("/api/kb/new_test_kb")
    assert resp.status_code == 200

    # Gone
    resp = client.delete("/api/kb/new_test_kb")
    assert resp.status_code == 404


def test_invalid_kb_name(client, temp_dir):
    for bad_name in ["test/kb", "test:kb", "test.kb"]:
        resp = client.post("/api/kb/create", json={"name": bad_name})
        assert resp.status_code == 400, f"Expected 400 for '{bad_name}', got {resp.status_code}"


# ── Chat ──


def test_chat_no_index_returns_400(client, temp_dir):
    """KB without built index should 400."""
    resp = client.post("/api/chat", json={
        "question": "东巴文化是什么？",
        "knowledge_base": "test_dongba",
    })
    assert resp.status_code == 400
    assert "index not built" in resp.json()["detail"]


# ── History ──


def test_history_roundtrip(client, temp_dir):
    # Patch HISTORY_DIR for all dependent modules
    tmp = tempfile.mkdtemp()
    patchers = [
        patch.object(backend.config, "HISTORY_DIR", Path(tmp)),
        patch.object(backend.history, "HISTORY_DIR", Path(tmp)),
    ]
    for p in patchers:
        p.start()

    try:
        # Should be empty
        resp = client.get("/api/history?session_id=default")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

        # List sessions
        resp = client.get("/api/history/sessions")
        assert resp.status_code == 200
    finally:
        for p in patchers:
            p.stop()
        shutil.rmtree(tmp)
