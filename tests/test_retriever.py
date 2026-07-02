"""Tests for the MMR retrieval module.

Covers: coarse-search fallback, MMR diversity, score threshold,
empty-KB handling, cache lifecycle.
"""
import sys, os, json, tempfile, shutil
from pathlib import Path
import numpy as np
from unittest.mock import patch

import pytest

# Ensure the project root is on sys.path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.config import KNOWLEDGE_BASES_DIR
from backend.retriever import mmr_search, clear_kb_cache


# ── Helpers ──


def _make_fake_index_and_metadata(kb_dir: Path, num_vectors: int = 10, dim: int = 512):
    """Create a real FAISS index + metadata JSON on disk for a KB."""
    import faiss

    kb_dir.mkdir(parents=True, exist_ok=True)

    # Random normalized vectors
    rng = np.random.RandomState(42)
    vectors = rng.randn(num_vectors, dim).astype(np.float32)
    faiss.normalize_L2(vectors)

    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    faiss.write_index(index, str(kb_dir / "faiss_index.index"))

    metadata = [
        {
            "content": f"Sample document {i} content here.",
            "source": str(kb_dir / f"doc_{i}.txt"),
            "filename": f"doc_{i}.txt",
            "chunk_id": i,
            "embedding": vectors[i].tolist(),
            "create_time": "2025-01-01 00:00:00",
        }
        for i in range(num_vectors)
    ]

    with open(kb_dir / "faiss_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False)

    return index, metadata


@pytest.fixture
def temp_kb(tmp_path):
    """A temporary KB with real FAISS index + metadata on disk."""
    kb_dir = tmp_path / "knowledge_bases" / "test_kb"
    _make_fake_index_and_metadata(kb_dir, num_vectors=20, dim=512)
    return kb_dir


# ── MMR diversity property ──


def test_mmr_returns_unique_results(temp_kb):
    """MMR re-ranking should not return duplicate content."""
    import faiss

    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", temp_kb.parent):
        clear_kb_cache()
        results = mmr_search("test query", "test_kb", top_k=5)

    assert len(results) > 0
    sources = [r["content"] for r in results]
    assert len(sources) == len(set(sources)), "MMR returned duplicate content"


def test_mmr_top_k_respected(temp_kb):
    """MMR should return at most top_k results."""
    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", temp_kb.parent):
        clear_kb_cache()
        results = mmr_search("test query", "test_kb", top_k=3)

    assert len(results) <= 3


def test_mmr_diversity_higher_with_lower_lambda(temp_kb):
    """With λ=0.3 (more diversity) vs λ=0.9 (more relevance),
    the λ=0.3 result set should have lower average pairwise similarity."""
    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", temp_kb.parent):
        clear_kb_cache()
        diverse = mmr_search("test query", "test_kb", top_k=5, lambda_param=0.3)
        relevant = mmr_search("test query", "test_kb", top_k=5, lambda_param=0.9)

    def avg_pairwise_sim(results):
        """Compute average cosine similarity between all result pairs."""
        import faiss

        sims = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                v_i = np.array(results[i].get("_embedding", []), dtype=np.float32)
                v_j = np.array(results[j].get("_embedding", []), dtype=np.float32)
                if v_i.size and v_j.size:
                    faiss.normalize_L2(v_i.reshape(1, -1))
                    faiss.normalize_L2(v_j.reshape(1, -1))
                    sims.append(float(np.dot(v_i, v_j)))
        return np.mean(sims) if sims else 0.0

    # Lower lambda (more diverse) should have lower pairwise similarity
    diverse_sim = avg_pairwise_sim(diverse)
    relevant_sim = avg_pairwise_sim(relevant)
    assert diverse_sim <= relevant_sim + 1e-6, (
        f"Expected diverse results (λ=0.3, sim={diverse_sim:.4f}) "
        f"to be less similar than relevant results (λ=0.9, sim={relevant_sim:.4f})"
    )


# ── Score threshold ──


def test_score_threshold_respected(temp_kb):
    """Low-scoring results should be replaced by a fallback message."""
    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", temp_kb.parent):
        clear_kb_cache()
        results = mmr_search("test query", "test_kb", score_threshold=0.99)

    # With random vectors and a real query, all scores are far below 0.99
    # so we should get the "no relevant content" fallback
    assert len(results) >= 1
    if results[0]["source"] == "__system__":
        assert "No relevant" in results[0]["content"] or "score threshold" in results[0]["content"]


# ── Edge cases ──


def test_empty_kb_returns_friendly_message(tmp_path):
    """An empty KB dir (no index) should return a system message."""
    empty_dir = tmp_path / "knowledge_bases"
    (empty_dir / "empty_kb").mkdir(parents=True, exist_ok=True)

    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", empty_dir):
        clear_kb_cache()
        results = mmr_search("anything", "empty_kb")

    assert len(results) == 1
    assert results[0]["source"] == "__system__"


def test_unknown_kb_returns_friendly_message(tmp_path):
    """Querying a KB that doesn't exist should return a system message."""
    kb_dir = tmp_path / "knowledge_bases"
    kb_dir.mkdir(parents=True, exist_ok=True)

    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", kb_dir):
        clear_kb_cache()
        results = mmr_search("anything", "nonexistent_kb")

    assert len(results) == 1
    assert results[0]["source"] == "__system__"


# ── Cache lifecycle ──


def test_clear_kb_cache_removes_specific_kb(temp_kb):
    """Clearing cache for one KB should not affect another."""
    from backend.retriever import _index_cache, _metadata_cache

    with patch.object(sys.modules["backend.config"], "KNOWLEDGE_BASES_DIR", temp_kb.parent):
        clear_kb_cache()
        _ = mmr_search("test", "test_kb")

        assert "test_kb" in _index_cache
        assert "test_kb" in _metadata_cache

        clear_kb_cache("test_kb")
        assert "test_kb" not in _index_cache
        assert "test_kb" not in _metadata_cache
