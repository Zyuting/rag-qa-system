"""Tests for the embedding module.

Covers: basic encoding, empty input, embedding dimension.
"""
import sys, os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.embedder import generate_embeddings, save_embeddings, load_embeddings, encode_query
from backend.config import EMBEDDING_MODEL_PATH


SKIP_IF_NO_MODEL = pytest.mark.skipif(
    not os.path.isdir(EMBEDDING_MODEL_PATH),
    reason="Embedding model not found locally; download first",
)


@SKIP_IF_NO_MODEL
def test_generate_embeddings_basic():
    chunks = [{"content": "东巴文化是纳西族的传统文化。", "source": "/fake/a.txt", "filename": "a.txt", "chunk_id": 0}]
    result = generate_embeddings(chunks, batch_size=16)
    assert len(result) == 1
    assert "embedding" in result[0]
    assert len(result[0]["embedding"]) == 512  # bge-small-zh-v1.5


@SKIP_IF_NO_MODEL
def test_empty_chunks():
    assert generate_embeddings([]) == []


@SKIP_IF_NO_MODEL
def test_embedding_dimension():
    chunks = [{"content": "test", "source": "/fake/t.txt", "filename": "t.txt", "chunk_id": i} for i in range(3)]
    result = generate_embeddings(chunks, batch_size=2)
    assert len(result) == 3
    for r in result:
        assert len(r["embedding"]) == 512


@SKIP_IF_NO_MODEL
def test_save_and_load_embeddings(tmp_path):
    chunks = [{"content": "test", "source": "/fake/t.txt", "filename": "t.txt", "chunk_id": 0}]
    embeddings = generate_embeddings(chunks)
    saved = save_embeddings(embeddings, "test_kb")

    from backend.config import KNOWLEDGE_BASES_DIR
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("backend.embedder.KNOWLEDGE_BASES_DIR", tmp_path)
        loaded = load_embeddings("test_kb")

    assert len(loaded) == 1
    assert "embedding" in loaded[0]
