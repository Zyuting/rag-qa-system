#!/usr/bin/env python3
# ==========================
# 知识库批量构建脚本
# 一次性构建所有知识库的 Chunk + Embedding + FAISS 索引
# ==========================
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.rag_02_zhishiku_jiazai import list_knowledge_bases
from backend.rag_03_wendang_qiefen import build_chunks
from backend.rag_04_xiangliang_bianma import generate_embeddings, save_embeddings
from backend.rag_05_faiss_goujian import build_faiss_index


def main():
    print("=" * 60)
    print("  云南非遗知识库批量构建工具")
    print("=" * 60)

    start = time.time()
    kbs = list_knowledge_bases()
    print(f"\n发现 {len(kbs)} 个知识库: {', '.join(kbs)}\n")

    total_chunks = 0
    total_vectors = 0
    failed = []

    for i, kb_name in enumerate(kbs, 1):
        print(f"[{i}/{len(kbs)}] 正在处理: {kb_name}")
        print("-" * 40)

        try:
            # Step 1: 切分
            chunks = build_chunks(kb_name)
            if not chunks:
                print(f"  ⚠ 跳过: 无有效文档\n")
                continue
            print(f"  ✓ Step 1/3: 切分完成 ({len(chunks)} chunks)")

            # Step 2: Embedding
            embeddings = generate_embeddings(chunks)
            save_path = save_embeddings(embeddings, kb_name)
            print(f"  ✓ Step 2/3: Embedding 完成 ({len(embeddings)} 条)")

            # Step 3: FAISS
            index, metadata = build_faiss_index(kb_name, embeddings)
            print(f"  ✓ Step 3/3: FAISS 索引完成 ({index.ntotal} 条向量)")

            total_chunks += len(chunks)
            total_vectors += index.ntotal
            print()

        except Exception as e:
            print(f"  ✗ 失败: {e}\n")
            failed.append((kb_name, str(e)))

    elapsed = time.time() - start

    print("=" * 60)
    print("  构建汇总")
    print("=" * 60)
    print(f"  知识库总数: {len(kbs)}")
    print(f"  成功: {len(kbs) - len(failed)}")
    print(f"  失败: {len(failed)}")
    print(f"  Chunk 总数: {total_chunks}")
    print(f"  向量总数: {total_vectors}")
    print(f"  总耗时: {elapsed:.1f}s")
    print("=" * 60)

    if failed:
        print("\n失败列表:")
        for name, err in failed:
            print(f"  - {name}: {err}")

    print("\n✅ 知识库构建完成！现在可以启动后端服务了。")
    print("   启动命令: cd backend && python rag_01_app.py")


if __name__ == "__main__":
    main()