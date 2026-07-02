"""Text chunking with overlap for document splitting."""
import os
from backend.config import KNOWLEDGE_BASES_DIR, CHUNKS_FILE, CHUNK_SIZE, CHUNK_OVERLAP


def split_documents(
    documents: list[dict],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """Split documents into chunks with paragraph-aware boundaries.

    Chunks that exceed chunk_size are split using a sliding window.
    Normal paragraphs are concatenated until chunk_size is reached,
    then a new chunk starts with trailing overlap content.

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

        paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
        total_paragraphs += len(paragraphs)
        current_chunk = ""

        for para in paragraphs:
            if len(para) > chunk_size:
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "source": doc["source"], "filename": doc["filename"],
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
                            "source": doc["source"], "filename": doc["filename"],
                            "chunk_id": chunk_id,
                        })
                        chunk_id += 1
                continue

            if len(current_chunk) + len(para) + 1 <= chunk_size:
                current_chunk += para + "\n"
            else:
                if current_chunk.strip():
                    chunks.append({
                        "content": current_chunk.strip(),
                        "source": doc["source"], "filename": doc["filename"],
                        "chunk_id": chunk_id,
                    })
                    chunk_id += 1

                overlap = current_chunk[-chunk_overlap:] if chunk_overlap < len(current_chunk) else current_chunk
                current_chunk = overlap + "\n" + para + "\n"

        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "source": doc["source"], "filename": doc["filename"],
                "chunk_id": chunk_id,
            })
            chunk_id += 1

    print(f"[INFO] Chunking: {len(documents)} docs → {total_paragraphs} paragraphs → {len(chunks)} chunks")
    return chunks


def save_chunks_to_file(chunks: list[dict], kb_name: str) -> str:
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)
    output_path = kb_dir / CHUNKS_FILE
    with open(output_path, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(f"========== Chunk {c['chunk_id']} ==========\n")
            f.write(f"File: {c['filename']}\nSource: {c['source']}\n\n{c['content']}\n\n")
    print(f"[INFO] chunks saved: {output_path}")
    return str(output_path)


def build_chunks(kb_name: str) -> list[dict]:
    """Full chunk pipeline: load → split → save."""
    from backend.loader import load_documents

    docs = load_documents(kb_name)
    if not docs:
        print(f"[WARN] KB [{kb_name}] has no documents")
        return []

    chunks = split_documents(docs)
    save_chunks_to_file(chunks, kb_name)
    return chunks


def build_all_chunks() -> dict[str, int]:
    from backend.loader import list_knowledge_bases

    kbs = list_knowledge_bases()
    print(f"\nBuilding chunks for {len(kbs)} KBs")
    results = {}
    for name in kbs:
        try:
            print(f"\n-- {name} --")
            chunks = build_chunks(name)
            results[name] = len(chunks)
            print(f"  → {len(chunks)} chunks")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results[name] = 0

    print(f"\nTotal: {sum(results.values())} chunks across {len(results)} KBs")
    return results


if __name__ == "__main__":
    build_all_chunks()
