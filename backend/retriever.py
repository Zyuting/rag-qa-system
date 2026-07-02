"""MMR (Maximal Marginal Relevance) retrieval module.

Pipeline: FAISS coarse search → MMR re-ranking → top-N results.
MMR balances relevance and diversity:
    mmr = λ·sim(q,d_i) − (1−λ)·max sim(d_i,d_j)
"""
import numpy as np
import faiss
from backend.config import (
    MMR_FETCH_K, MMR_TOP_K, MMR_LAMBDA, MMR_SCORE_THRESHOLD, EMBEDDING_MODEL_PATH,
)

_index_cache: dict[str, "faiss.IndexFlatIP"] = {}
_metadata_cache: dict[str, list[dict]] = {}
_query_encoder = None


def _get_query_encoder():
    if _query_encoder is None:
        import os
        from sentence_transformers import SentenceTransformer
        os.environ["DISABLE_TQDM"] = "1"
        _query_encoder = SentenceTransformer(EMBEDDING_MODEL_PATH, device="cpu")
    return _query_encoder


def _ensure_kb_loaded(kb_name: str):
    if kb_name not in _index_cache or kb_name not in _metadata_cache:
        from backend.indexer import load_faiss_index
        index, metadata = load_faiss_index(kb_name)
        _index_cache[kb_name] = index
        _metadata_cache[kb_name] = metadata


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    return float(np.dot(vec_a, vec_b))


def mmr_search(
    query: str,
    kb_name: str,
    top_k: int = MMR_TOP_K,
    fetch_k: int = MMR_FETCH_K,
    lambda_param: float = MMR_LAMBDA,
    score_threshold: float = MMR_SCORE_THRESHOLD,
) -> list[dict]:
    """
    MMR (Maximal Marginal Relevance) search.

    Pipeline: encode query → FAISS coarse search (Top-fetch_k) → MMR re-rank (Top-top_k).

    MMR balances relevance and diversity:
        mmr = λ · sim(q, d_i) - (1-λ) · max sim(d_i, d_j)

    Args:
        query: User question text.
        kb_name: Knowledge base name.
        top_k: Number of results to return.
        fetch_k: Number of candidates to fetch from FAISS.
        lambda_param: MMR lambda (higher = more relevance-focused).
        score_threshold: Minimum relevance score to return any result.

    Returns:
        [{content, source, filename, score}, ...]
    """
    # load KB
    try:
        _ensure_kb_loaded(kb_name)
    except FileNotFoundError:
        return [{
            "content": f"Knowledge base [{kb_name}] index not built yet.",
            "source": "__system__",
            "filename": "__system__",
            "score": 0.0,
        }]

    index = _index_cache[kb_name]
    metadata = _metadata_cache[kb_name]

    if index.ntotal == 0:
        return [{
            "content": "Knowledge base is empty.",
            "source": "__system__",
            "filename": "__system__",
            "score": 0.0,
        }]

    # encode query
    encoder = _get_query_encoder()
    query_vec = encoder.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(query_vec)

    # FAISS coarse search
    actual_fetch_k = min(fetch_k, index.ntotal)
    scores, indices = index.search(query_vec, actual_fetch_k)

    # build candidates
    candidates = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        emb = np.array(metadata[idx]["embedding"], dtype=np.float32)
        faiss.normalize_L2(emb.reshape(1, -1))
        candidates.append({
            "idx": int(idx),
            "vector": emb,
            "score": float(score),
        })

    if not candidates:
        return [{
            "content": "No relevant content found.",
            "source": "__system__",
            "filename": "__system__",
            "score": 0.0,
        }]

    # threshold filter
    max_score = candidates[0]["score"]
    if max_score < score_threshold:
        return [{
            "content": "No relevant content found above the score threshold.",
            "source": "__system__",
            "filename": "__system__",
            "score": float(max_score),
        }]

    # MMR re-ranking
    candidate_vecs = np.array([c["vector"] for c in candidates], dtype=np.float32)
    relevance = np.array([c["score"] for c in candidates], dtype=np.float32)

    selected = [int(np.argmax(relevance))]
    actual_top_k = min(top_k, len(candidates))

    while len(selected) < actual_top_k:
        best_idx = -1
        best_mmr = -float("inf")

        for i in range(len(candidates)):
            if i in selected:
                continue

            # relevance score
            rel = relevance[i]

            # diversity penalty: max similarity to already-selected items
            max_sim = max(
                _cosine_similarity(candidate_vecs[i], candidate_vecs[j])
                for j in selected
            )

            mmr = lambda_param * rel - (1.0 - lambda_param) * max_sim

            if mmr > best_mmr:
                best_mmr = mmr
                best_idx = i

        if best_idx < 0:
            break
        selected.append(best_idx)

    # assemble results
    results = []
    for pos in selected:
        real_idx = candidates[pos]["idx"]
        meta = metadata[real_idx]
        results.append({
            "content": meta["content"],
            "source": meta.get("source", ""),
            "filename": meta.get("filename", ""),
            "score": float(relevance[pos]),
        })

    return results


def clear_kb_cache(kb_name: str | None = None):
    """Clear the index/metadata cache. Call after KB updates."""
    global _index_cache, _metadata_cache
    if kb_name is None:
        _index_cache.clear()
        _metadata_cache.clear()
        print("[INFO] All caches cleared")
    else:
        _index_cache.pop(kb_name, None)
        _metadata_cache.pop(kb_name, None)
        print(f"[INFO] Cache cleared for [{kb_name}]")


if __name__ == "__main__":
    from backend.loader import list_knowledge_bases

    kbs = list_knowledge_bases()
    if kbs:
        kb = kbs[0]
        print(f"KB: {kb}")
        results = mmr_search("东巴文化是什么？", kb)
        for i, r in enumerate(results):
            print(f"\n-- Result {i+1} (score={r['score']:.4f}) --")
            print(f"Source: {r['filename']}")
            print(f"Content: {r['content'][:200]}...")