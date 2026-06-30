import sys, os

# 项目根目录
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
os.environ["PYTHONPATH"] = BASE

# 确保使用正确的 embedding 模型路径
from backend.config import EMBEDDING_MODEL_PATH, KNOWLEDGE_BASES_DIR, INDEX_FILE

import uvicorn

if __name__ == "__main__":
    print(f"Python: {sys.executable}")
    print(f"Project: {BASE}")
    print(f"KB dir: {KNOWLEDGE_BASES_DIR}")
    print(f"Model: {EMBEDDING_MODEL_PATH}")

    uvicorn.run(
        "backend.rag_01_app:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info",
    )