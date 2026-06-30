# ==========================
# 全局配置
# ==========================
import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件
load_dotenv(BASE_DIR / ".env")

# ─────────────── API 密钥 ───────────────
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://api.qwen.ai/v1")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")

# ─────────────── 路径 ───────────────
KNOWLEDGE_BASES_DIR = BASE_DIR / "knowledge_bases"
EMBEDDING_MODEL_PATH = str(BASE_DIR / "bge-small-zh-v1.5")

# ─────────────── 知识库文件 ───────────────
CHUNKS_FILE = "chunks.txt"
EMBEDDINGS_FILE = "chunk_embeddings.json"
INDEX_FILE = "faiss_index.index"
METADATA_FILE = "faiss_metadata.json"

# ─────────────── 切分参数 ───────────────
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
BATCH_SIZE = 16

# ─────────────── 检索参数 ───────────────
MMR_FETCH_K = 20
MMR_TOP_K = 5
MMR_LAMBDA = 0.7
MMR_SCORE_THRESHOLD = 0.01

# ─────────────── 对话历史 ───────────────
HISTORY_DIR = BASE_DIR / "conversation_history"
MAX_HISTORY_ROUNDS = 20

# ─────────────── 支持文档类型 ───────────────
SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx", ".html"]
