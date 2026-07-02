"""Embedding generation using bge-small-zh-v1.5 (sentence-transformers).

Batch-encodes text chunks into 512-d float vectors, persists to JSON.
"""
import os, json, time
import numpy as np
from backend.config import (
    KNOWLEDGE_BASES_DIR, EMBEDDINGS_FILE, EMBEDDING_MODEL_PATH, BATCH_SIZE,
)

try:
    import torch  # noqa: F401 — early import to avoid DLL race
except Exception:
    pass

_embedding_model = None


def _get_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        print(f"[INFO] Loading embedding model: {EMBEDDING_MODEL_PATH}")
        os.environ["DISABLE_TQDM"] = "1"
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_PATH, device="cpu")
        print("[INFO] Embedding model loaded")
    return _embedding_model


def generate_embeddings(chunks: list[dict], batch_size: int = BATCH_SIZE) -> list[dict]:
    """Batch-encode chunks into embedding vectors.

    Returns:
        [{..., "embedding": [float, ...]}, ...]
    """
    if not chunks:
        print("[WARN] Empty chunks, skipping")
        return []

    model = _get_model()
    start = time.time()
    embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c["content"] for c in batch if c["content"].strip()]
        if not texts:
            continue

        try:
            vectors = model.encode(texts, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False)
        except Exception as e:
            print(f"[ERROR] Batch {i}-{min(i + batch_size, len(chunks))} encode failed: {e}")
            continue

        for chunk, vec in zip(batch, vectors):
            embeddings.append({
                "content": chunk["content"], "source": chunk.get("source", ""),
                "filename": chunk.get("filename", ""), "chunk_id": chunk.get("chunk_id", i),
                "embedding": vec.tolist(),
            })

        print(f"[INFO] Encoded {min(i + batch_size, len(chunks))}/{len(chunks)}")

    print(f"[INFO] Embedding done: {len(embeddings)} vectors in {time.time()-start:.1f}s")
    return embeddings


def save_embeddings(embeddings: list[dict], kb_name: str) -> str:
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)
    path = kb_dir / EMBEDDINGS_FILE
    with open(path, "w", encoding="utf-8") as f:
        json.dump(embeddings, f, ensure_ascii=False, separators=(",", ":"))
    print(f"[INFO] Embeddings saved: {path} ({path.stat().st_size / 1024**2:.1f} MB)")
    return str(path)


def load_embeddings(kb_name: str) -> list[dict]:
    path = KNOWLEDGE_BASES_DIR / kb_name / EMBEDDINGS_FILE
    if not path.exists():
        print(f"[WARN] Embeddings file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"[INFO] Loaded {len(data)} embeddings from [{kb_name}]")
    return data


def encode_query(query: str) -> np.ndarray:
    model = _get_model()
    return model.encode([query], convert_to_numpy=True, show_progress_bar=False).astype(np.float32)


if __name__ == "__main__":
    from backend.loader import list_knowledge_bases, load_documents
    from backend.chunker import split_documents

    kbs = list_knowledge_bases()
    if kbs:
        kb = kbs[0]
        print(f"Testing KB: {kb}")
        docs = load_documents(kb)
        chunks = split_documents(docs)
        embs = generate_embeddings(chunks)
        save_embeddings(embs, kb)
        print(f"Vector dim: {len(embs[0]['embedding']) if embs else 'N/A'}")
