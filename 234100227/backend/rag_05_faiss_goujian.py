# ==========================
# 模块 05：FAISS 索引构建
# 功能：基于 embedding 构建 FAISS 向量索引
#       输出 faiss_index.index + faiss_metadata.json
# ==========================
import os
import json
import time
import numpy as np
import faiss
from backend.config import (
    KNOWLEDGE_BASES_DIR,
    INDEX_FILE,
    METADATA_FILE,
    EMBEDDINGS_FILE,
)


def build_faiss_index(
    kb_name: str,
    embeddings: list[dict] | None = None,
) -> tuple:
    """
    为指定知识库构建 FAISS 余弦相似度索引（内积 = L2归一化后余弦）

    Args:
        kb_name: 知识库名称
        embeddings: embedding 列表，为 None 则从 JSON 加载

    Returns:
        (faiss_index, metadata_list)
    """
    # ── 加载 embedding ──
    if embeddings is None:
        emb_path = KNOWLEDGE_BASES_DIR / kb_name / EMBEDDINGS_FILE
        if not emb_path.exists():
            raise FileNotFoundError(
                f"Embedding 文件不存在: {emb_path}\n"
                f"请先运行 build_kb.py 构建知识库"
            )
        with open(emb_path, "r", encoding="utf-8") as f:
            embeddings = json.load(f)

    valid = [e for e in embeddings if e.get("embedding")]
    if not valid:
        raise ValueError(f"知识库 [{kb_name}] 无有效 embedding")

    # ── 构建向量矩阵 ──
    vectors = np.array([e["embedding"] for e in valid], dtype=np.float32)

    # L2 归一化 → 内积等价于余弦相似度
    faiss.normalize_L2(vectors)

    dim = vectors.shape[1]
    print(f"[INFO] FAISS 维度: {dim}, 向量数: {vectors.shape[0]}")

    # ── 创建索引 ──
    index = faiss.IndexFlatIP(dim)  # Inner Product (余弦相似度)
    index.add(vectors)

    # ── 保存索引 ──
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)

    # 先 cd 到知识库目录（避免中文路径导致 FAISS C++ fopen 失败）
    old_cwd = os.getcwd()
    os.chdir(str(kb_dir))
    faiss.write_index(index, INDEX_FILE)
    os.chdir(old_cwd)
    print(f"[INFO] FAISS 索引已保存: {kb_dir / INDEX_FILE}")

    # ── 保存元数据 ──
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    metadata = []
    for e in valid:
        metadata.append({
            "content": e["content"],
            "source": e.get("source", ""),
            "filename": e.get("filename", ""),
            "chunk_id": e.get("chunk_id", 0),
            "embedding": e["embedding"],
            "create_time": now,
        })

    meta_path = kb_dir / METADATA_FILE
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, separators=(",", ":"))

    meta_size_mb = meta_path.stat().st_size / (1024 * 1024)
    print(f"[INFO] 元数据已保存: {meta_path} ({meta_size_mb:.1f} MB)")

    return index, metadata


def load_faiss_index(kb_name: str) -> tuple:
    """
    加载指定知识库的 FAISS 索引和元数据

    Returns:
        (faiss_index, metadata_list)
    """
    index_path = KNOWLEDGE_BASES_DIR / kb_name / INDEX_FILE
    meta_path = KNOWLEDGE_BASES_DIR / kb_name / METADATA_FILE

    if not index_path.exists():
        raise FileNotFoundError(
            f"FAISS 索引不存在: {index_path}\n"
            f"请先运行 build_kb.py 构建知识库"
        )
    if not meta_path.exists():
        raise FileNotFoundError(f"元数据文件不存在: {meta_path}")

    # 先 cd 到知识库目录再读取（避免中文路径问题）
    old_cwd = os.getcwd()
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    os.chdir(str(kb_dir))
    index = faiss.read_index(INDEX_FILE)
    os.chdir(old_cwd)

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(
        f"[INFO] 加载 FAISS 索引 [{kb_name}]: "
        f"{index.ntotal} 条向量, 维度 {index.d}"
    )
    return index, metadata


def index_exists(kb_name: str) -> bool:
    """检查知识库索引是否已构建"""
    index_path = KNOWLEDGE_BASES_DIR / kb_name / INDEX_FILE
    meta_path = KNOWLEDGE_BASES_DIR / kb_name / METADATA_FILE
    return index_path.exists() and meta_path.exists()


def build_all_indexes() -> dict[str, int]:
    """
    为所有知识库构建 FAISS 索引

    Returns:
        {kb_name: vector_count, ...}
    """
    from backend.rag_02_zhishiku_jiazai import list_knowledge_bases
    from backend.rag_04_xiangliang_bianma import load_embeddings

    kb_names = list_knowledge_bases()
    print(f"\n{'='*50}")
    print(f"批量构建 FAISS 索引: 共 {len(kb_names)} 个知识库")
    print(f"{'='*50}")

    result = {}
    for kb_name in kb_names:
        try:
            print(f"\n── {kb_name} ──")
            embeddings = load_embeddings(kb_name)
            if not embeddings:
                print(f"  [SKIP] 无 embedding，请先运行 build_kb.py")
                result[kb_name] = 0
                continue
            _, meta = build_faiss_index(kb_name, embeddings)
            result[kb_name] = len(meta)
            print(f"  → {len(meta)} 条向量")
        except Exception as e:
            print(f"[ERROR] {kb_name} 构建失败: {e}")
            result[kb_name] = 0

    total = sum(result.values())
    print(f"\n{'='*50}")
    print(f"汇总: {len(result)} 个知识库, 共 {total} 条向量")
    print(f"{'='*50}")
    return result


# ==========================
# 测试入口
# ==========================
if __name__ == "__main__":
    build_all_indexes()
