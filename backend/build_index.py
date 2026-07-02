#!/usr/bin/env python3
"""Batch build vector indexes for all knowledge bases."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.loader import list_knowledge_bases
from backend.chunker import build_chunks
from backend.embedder import generate_embeddings, save_embeddings
from backend.indexer import build_faiss_index


def main():
    print("=" * 60)
    print("  Yuti RAG — Index Builder")
    print("=" * 60)

    start = time.time()
    kbs = list_knowledge_bases()
    print(f"\nFound {len(kbs)} KBs: {', '.join(kbs)}\n")

    total_chunks = 0
    total_vectors = 0
    failed = []

    for i, kb_name in enumerate(kbs, 1):
        print(f"[{i}/{len(kbs)}] Processing: {kb_name}")
        print("-" * 40)

        try:
            chunks = build_chunks(kb_name)
            if not chunks:
                print(f"  SKIP: no documents\n")
                continue
            print(f"  ✓ Chunked: {len(chunks)} chunks")

            embeddings = generate_embeddings(chunks)
            save_embeddings(embeddings, kb_name)
            print(f"  ✓ Embedded: {len(embeddings)} vectors")

            index, metadata = build_faiss_index(kb_name, embeddings)
            print(f"  ✓ Indexed: {index.ntotal} vectors")

            total_chunks += len(chunks)
            total_vectors += index.ntotal
            print()

        except Exception as e:
            print(f"  FAILED: {e}\n")
            failed.append((kb_name, str(e)))

    elapsed = time.time() - start

    print("=" * 60)
    print("  Summary")
    print("=" * 60)
    print(f"  KBs: {len(kbs)}")
    print(f"  Succeeded: {len(kbs) - len(failed)}")
    print(f"  Failed: {len(failed)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Total vectors: {total_vectors}")
    print(f"  Elapsed: {elapsed:.1f}s")
    print("=" * 60)

    if failed:
        print("\nFailures:")
        for name, err in failed:
            print(f"  - {name}: {err}")

    print("\nDone. Start the API server with:")
    print("  python -m uvicorn backend.main:app --reload --port 8001")


if __name__ == "__main__":
    main()