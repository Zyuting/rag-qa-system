"""FAISS vector index builder.

Builds IndexFlatIP (inner product → cosine similarity after L2 normalization).
Persists index and metadata to disk.
"""
import os, json, time
import numpy as np
import faiss
from backend.config import KNOWLEDGE_BASES_DIR, INDEX_FILE, METADATA_FILE, EMBEDDINGS_FILE


def build_faiss_index(kb_name: str, embeddings: list[dict] | None = None) -> tuple:
    """Build a FAISS cosine similarity index for a knowledge base.

    Args:
        kb_name: Knowledge base name.
        embeddings: Optional pre-loaded embeddings list. Loads from disk if None.

    Returns:
        (faiss_index, metadata_list)
    """
    if embeddings is None:
        emb_path = KNOWLEDGE_BASES_DIR / kb_name / EMBEDDINGS_FILE
        if not emb_path.exists():
            raise FileNotFoundError(f"Embeddings file not found: {emb_path}. Run build_index.py first.")
        with open(emb_path, "r", encoding="utf-8") as f:
            embeddings = json.load(f)

    valid = [e for e in embeddings if e.get("embedding")]
    if not valid:
        raise ValueError(f"KB [{kb_name}] has no valid embeddings")

    vectors = np.array([e["embedding"] for e in valid], dtype=np.float32)
    faiss.normalize_L2(vectors)

    dim = vectors.shape[1]
    print(f"[INFO] FAISS dim={dim}, vectors={vectors.shape[0]}")

    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)

    # chdir to avoid FAISS C++ fopen issues with non-ASCII paths
    old_cwd = os.getcwd()
    os.chdir(str(kb_dir))
    faiss.write_index(index, INDEX_FILE)
    os.chdir(old_cwd)
    print(f"[INFO] FAISS index saved: {kb_dir / INDEX_FILE}")

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    metadata = [
        {
            "content": e["content"], "source": e.get("source", ""),
            "filename": e.get("filename", ""), "chunk_id": e.get("chunk_id", 0),
            "embedding": e["embedding"], "create_time": now,
        }
        for e in valid
    ]

    meta_path = kb_dir / METADATA_FILE
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, separators=(",", ":"))

    print(f"[INFO] Metadata saved: {meta_path} ({meta_path.stat().st_size / 1024**2:.1f} MB)")
    return index, metadata


def load_faiss_index(kb_name: str) -> tuple:
    """Load a FAISS index and its metadata from disk.

    Returns:
        (faiss_index, metadata_list)
    """
    index_path = KNOWLEDGE_BASES_DIR / kb_name / INDEX_FILE
    meta_path = KNOWLEDGE_BASES_DIR / kb_name / METADATA_FILE

    if not index_path.exists():
        raise FileNotFoundError(f"FAISS index not found: {index_path}. Run build_index.py first.")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadata not found: {meta_path}")

    old_cwd = os.getcwd()
    os.chdir(str(KNOWLEDGE_BASES_DIR / kb_name))
    index = faiss.read_index(INDEX_FILE)
    os.chdir(old_cwd)

    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"[INFO] Loaded FAISS index [{kb_name}]: {index.ntotal} vectors, dim={index.d}")
    return index, metadata


def index_exists(kb_name: str) -> bool:
    return (KNOWLEDGE_BASES_DIR / kb_name / INDEX_FILE).exists() and \
           (KNOWLEDGE_BASES_DIR / kb_name / METADATA_FILE).exists()


def build_all_indexes() -> dict[str, int]:
    from backend.loader import list_knowledge_bases
    from backend.embedder import load_embeddings

    kbs = list_knowledge_bases()
    print(f"\nBuilding FAISS indexes for {len(kbs)} KBs")
    results = {}
    for name in kbs:
        try:
            print(f"\n-- {name} --")
            embeddings = load_embeddings(name)
            if not embeddings:
                print("  [SKIP] No embeddings found")
                results[name] = 0
                continue
            _, meta = build_faiss_index(name, embeddings)
            results[name] = len(meta)
            print(f"  → {len(meta)} vectors")
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            results[name] = 0

    print(f"\nTotal: {sum(results.values())} vectors across {len(results)} KBs")
    return results


if __name__ == "__main__":
    build_all_indexes()
