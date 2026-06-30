# ==========================
# 模块 03：文档智能切分
# 功能：将长篇文档切分为固定大小的 chunk
#       chunk_size=500, chunk_overlap=100
# ==========================
import os
import json
from backend.config import KNOWLEDGE_BASES_DIR, CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP


def split_documents(
    documents: list[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    按段落边界智能切分文档，保持语义完整性

    Args:
        documents: load_documents() 返回的文档列表
        chunk_size: 每个 chunk 的目标字符数
        chunk_overlap: 相邻 chunk 重叠字符数

    Returns:
        [{"content": str, "source": str, "filename": str, "chunk_id": int}, ...]
    """
    chunks = []
    chunk_id = 0
    total_paragraphs = 0

    for doc in documents:
        text = doc.get("content", "").strip()
        if not text:
            continue

        # 按段落拆分
        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        total_paragraphs += len(paragraphs)

        current_chunk = ""

        for para in paragraphs:
            # ── 超长段落：滑动窗口切分 ──
            if len(para) > chunk_size:
                # 先保存当前 chunk
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "source": doc.get("source", ""),
                        "filename": doc.get("filename", ""),
                        "chunk_id": chunk_id,
                    })
                    chunk_id += 1
                    current_chunk = ""

                step = max(1, chunk_size - chunk_overlap)
                for i in range(0, len(para), step):
                    part = para[i:i + chunk_size].strip()
                    if part:
                        chunks.append({
                            "content": part,
                            "source": doc.get("source", ""),
                            "filename": doc.get("filename", ""),
                            "chunk_id": chunk_id,
                        })
                        chunk_id += 1
                continue

            # ── 正常拼接段落 ──
            if len(current_chunk) + len(para) + 1 <= chunk_size:
                current_chunk += para + "\n"
            else:
                # 当前 chunk 已满，保存
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "source": doc.get("source", ""),
                        "filename": doc.get("filename", ""),
                        "chunk_id": chunk_id,
                    })
                    chunk_id += 1

                # 新 chunk 带重叠
                overlap_text = (
                    current_chunk[-chunk_overlap:]
                    if chunk_overlap < len(current_chunk)
                    else current_chunk
                )
                current_chunk = overlap_text + "\n" + para + "\n"

        # ── 保存最后一个 chunk ──
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "source": doc.get("source", ""),
                "filename": doc.get("filename", ""),
                "chunk_id": chunk_id,
            })
            chunk_id += 1

    print(
        f"[INFO] 切分完成: {len(documents)} 文档 → "
        f"{total_paragraphs} 段落 → {len(chunks)} chunks"
    )
    return chunks


def save_chunks_to_file(chunks: list[dict], kb_name: str) -> str:
    """
    将 chunks 保存为可读的文本文件

    Returns:
        输出文件路径
    """
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)

    output_path = kb_dir / CHUNKS_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        for chunk in chunks:
            f.write(f"========== Chunk {chunk['chunk_id']} ==========\n")
            f.write(f"文件: {chunk['filename']}\n")
            f.write(f"来源: {chunk['source']}\n\n")
            f.write(chunk["content"])
            f.write("\n\n")

    print(f"[INFO] chunks.txt 已保存: {output_path}")
    return str(output_path)


def build_chunks(kb_name: str) -> list[dict]:
    """
    完整的 chunk 构建流程：加载 → 切分 → 保存
    """
    from backend.rag_02_zhishiku_jiazai import load_documents

    docs = load_documents(kb_name)
    if not docs:
        print(f"[WARN] 知识库 [{kb_name}] 无文档")
        return []

    chunks = split_documents(docs)
    save_chunks_to_file(chunks, kb_name)
    return chunks


def build_all_chunks() -> dict[str, int]:
    """
    批量构建所有知识库的 chunk

    Returns:
        {kb_name: chunk_count, ...}
    """
    from backend.rag_02_zhishiku_jiazai import list_knowledge_bases

    kb_names = list_knowledge_bases()
    print(f"\n{'='*50}")
    print(f"批量构建 Chunk: 共 {len(kb_names)} 个知识库")
    print(f"{'='*50}")

    result = {}
    for kb_name in kb_names:
        try:
            print(f"\n── {kb_name} ──")
            chunks = build_chunks(kb_name)
            result[kb_name] = len(chunks)
            print(f"  → {len(chunks)} chunks")
        except Exception as e:
            print(f"[ERROR] {kb_name} 构建失败: {e}")
            result[kb_name] = 0

    total = sum(result.values())
    print(f"\n{'='*50}")
    print(f"汇总: {len(result)} 个知识库, 共 {total} chunks")
    print(f"{'='*50}")
    return result


# ==========================
# 测试入口
# ==========================
if __name__ == "__main__":
    build_all_chunks()
