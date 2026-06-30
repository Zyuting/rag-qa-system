# ==========================
# 模块 04：Embedding 向量编码
# 功能：使用 bge-small-zh-v1.5 模型将 chunk 转为向量
#       输出 chunk_embeddings.json
# ==========================
import os
import json
import time
import numpy as np
from backend.config import (
    KNOWLEDGE_BASES_DIR,
    EMBEDDINGS_FILE,
    EMBEDDING_MODEL_PATH,
    BATCH_SIZE,
)

# Ensure torch is imported early to avoid intermittent DLL load permission errors
try:
    import torch  # noqa: F401
except Exception:
    # defer error to later when model is actually needed, but attempt early import
    pass

# ────── 全局模型缓存 ──────
_embedding_model = None


def _get_model():
    """懒加载 Embedding 模型（全局单例）"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer

        print(f"[INFO] 加载 Embedding 模型: {EMBEDDING_MODEL_PATH}")
        os.environ["DISABLE_TQDM"] = "1"
        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL_PATH,
            device="cpu",
        )
        print("[INFO] Embedding 模型加载完成")
    return _embedding_model


def generate_embeddings(
    chunks: list[dict],
    batch_size: int = BATCH_SIZE,
) -> list[dict]:
    """
    对 chunk 列表进行批量向量编码

    Args:
        chunks: split_documents() 返回的 chunk 列表
        batch_size: 批处理大小

    Returns:
        [{..., "embedding": [float, ...]}, ...]
    """
    if not chunks:
        print("[WARN] chunks 列表为空，跳过编码")
        return []

    model = _get_model()
    start_time = time.time()

    embeddings = []
    total = len(chunks)

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch if c["content"].strip()]

        if not texts:
            continue

        try:
            vectors = model.encode(
                texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=False,
            )
        except Exception as e:
            print(f"[ERROR] Batch {i}-{min(i + batch_size, total)} 编码失败: {e}")
            continue

        for chunk, vector in zip(batch, vectors):
            embeddings.append({
                "content": chunk["content"],
                "source": chunk.get("source", ""),
                "filename": chunk.get("filename", ""),
                "chunk_id": chunk.get("chunk_id", i),
                "embedding": vector.tolist(),
            })

        progress = min(i + batch_size, total)
        print(f"[INFO] 编码进度: {progress}/{total}")

    elapsed = time.time() - start_time
    print(f"[INFO] Embedding 生成完成: {len(embeddings)} 条, 耗时 {elapsed:.1f}s")
    return embeddings


def save_embeddings(embeddings: list[dict], kb_name: str) -> str:
    """
    保存 embedding 到 JSON 文件

    Returns:
        输出文件路径
    """
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)

    output_path = kb_dir / EMBEDDINGS_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(embeddings, f, ensure_ascii=False, separators=(",", ":"))

    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"[INFO] Embedding JSON 已保存: {output_path} ({file_size_mb:.1f} MB)")
    return str(output_path)


def load_embeddings(kb_name: str) -> list[dict]:
    """
    从 JSON 文件加载 embedding
    """
    file_path = KNOWLEDGE_BASES_DIR / kb_name / EMBEDDINGS_FILE
    if not file_path.exists():
        print(f"[WARN] Embedding 文件不存在: {file_path}")
        return []

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[INFO] 加载 {len(data)} 条 embedding 从 {kb_name}")
    return data


def encode_query(query: str) -> np.ndarray:
    """
    对单个查询文本进行向量编码
    """
    model = _get_model()
    vec = model.encode(
        [query],
        convert_to_numpy=True,
        show_progress_bar=False,
    ).astype(np.float32)
    return vec


# ==========================
# 测试入口
# ==========================
if __name__ == "__main__":
    from backend.rag_02_zhishiku_jiazai import list_knowledge_bases, load_documents
    from backend.rag_03_wendang_qiefen import split_documents

    kbs = list_knowledge_bases()
    if kbs:
        kb = kbs[0]
        print(f"测试知识库: {kb}")
        docs = load_documents(kb)
        chunks = split_documents(docs)
        embs = generate_embeddings(chunks)
        save_embeddings(embs, kb)
        print(f"向量维度: {len(embs[0]['embedding']) if embs else 'N/A'}")
