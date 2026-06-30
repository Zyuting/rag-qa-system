# ==========================
# 模块 06：MMR 检索模块
# 功能：FAISS 粗排 Top-K → MMR 重排序 → 返回 Top-N
#       MMR 平衡相关性和多样性，避免重复内容
# ==========================
import numpy as np
import faiss
from backend.config import (
    MMR_FETCH_K,
    MMR_TOP_K,
    MMR_LAMBDA,
    MMR_SCORE_THRESHOLD,
    EMBEDDING_MODEL_PATH,
)

# ────── 全局缓存：按知识库名缓存索引/元数据/模型 ──────
_index_cache: dict[str, "faiss.IndexFlatIP"] = {}
_metadata_cache: dict[str, list[dict]] = {}
_query_encoder = None


def _get_query_encoder():
    """懒加载查询编码器"""
    global _query_encoder
    if _query_encoder is None:
        import os
        from sentence_transformers import SentenceTransformer

        os.environ["DISABLE_TQDM"] = "1"
        _query_encoder = SentenceTransformer(EMBEDDING_MODEL_PATH, device="cpu")
    return _query_encoder


def _ensure_kb_loaded(kb_name: str):
    """确保指定知识库的索引和元数据已加载到缓存"""
    if kb_name not in _index_cache or kb_name not in _metadata_cache:
        from backend.rag_05_faiss_goujian import load_faiss_index

        index, metadata = load_faiss_index(kb_name)
        _index_cache[kb_name] = index
        _metadata_cache[kb_name] = metadata


def _cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """计算两个 L2 归一化向量的余弦相似度（即内积）"""
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
    MMR (Maximal Marginal Relevance) 检索

    流程：
    1. 编码查询向量
    2. FAISS 粗排召回 Top-fetch_k
    3. MMR 重排序选出 Top-top_k（平衡相关性 & 多样性）

    Args:
        query: 用户问题文本
        kb_name: 知识库名称
        top_k: 最终返回数量
        fetch_k: FAISS 粗排召回数量
        lambda_param: MMR 权衡参数 (越大越偏重相关性)
        score_threshold: 最低相似度阈值

    Returns:
        [{content, source, filename, score}, ...]
    """
    # ── 0. 加载知识库 ──
    try:
        _ensure_kb_loaded(kb_name)
    except FileNotFoundError as e:
        return [{
            "content": f"知识库 [{kb_name}] 尚未构建索引，请先在管理面板构建。",
            "source": "系统",
            "filename": "系统",
            "score": 0.0,
        }]

    index = _index_cache[kb_name]
    metadata = _metadata_cache[kb_name]

    if index.ntotal == 0:
        return [{
            "content": "知识库为空，无可用数据。",
            "source": "系统",
            "filename": "系统",
            "score": 0.0,
        }]

    # ── 1. 编码查询 ──
    encoder = _get_query_encoder()
    query_vec = encoder.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(query_vec)

    # ── 2. FAISS 粗排 ──
    actual_fetch_k = min(fetch_k, index.ntotal)
    scores, indices = index.search(query_vec, actual_fetch_k)

    # ── 3. 构建候选集 ──
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
            "content": "未检索到相关内容。",
            "source": "系统",
            "filename": "系统",
            "score": 0.0,
        }]

    # ── 4. 阈值过滤 ──
    max_score = candidates[0]["score"]
    if max_score < score_threshold:
        return [{
            "content": "抱歉，知识库中未找到与您问题高度相关的资料。请尝试换一种方式提问。",
            "source": "系统",
            "filename": "系统",
            "score": float(max_score),
        }]

    # ── 5. MMR 重排序 ──
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

            # 相关性得分
            rel = relevance[i]

            # 多样性惩罚：与已选中项的最大相似度
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

    # ── 6. 组装结果 ──
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
    """清除缓存（知识库更新后调用）"""
    global _index_cache, _metadata_cache
    if kb_name is None:
        _index_cache.clear()
        _metadata_cache.clear()
        print("[INFO] 已清除全部缓存")
    else:
        _index_cache.pop(kb_name, None)
        _metadata_cache.pop(kb_name, None)
        print(f"[INFO] 已清除 [{kb_name}] 缓存")


# ==========================
# 测试入口
# ==========================
if __name__ == "__main__":
    from backend.rag_02_zhishiku_jiazai import list_knowledge_bases

    kbs = list_knowledge_bases()
    if kbs:
        kb = kbs[0]
        print(f"测试知识库: {kb}")
        results = mmr_search("东巴文化是什么？", kb)
        for i, r in enumerate(results):
            print(f"\n── 结果 {i+1} (score={r['score']:.4f}) ──")
            print(f"来源: {r['filename']}")
            print(f"内容: {r['content'][:200]}...")