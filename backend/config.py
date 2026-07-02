# Global configuration
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# API keys
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")

# Paths
KNOWLEDGE_BASES_DIR = BASE_DIR / "knowledge_bases"
EMBEDDING_MODEL_PATH = str(BASE_DIR / "bge-small-zh-v1.5")

# File names
CHUNKS_FILE = "chunks.txt"
EMBEDDINGS_FILE = "chunk_embeddings.json"
INDEX_FILE = "faiss_index.index"
METADATA_FILE = "faiss_metadata.json"

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
BATCH_SIZE = 16

# Retrieval
MMR_FETCH_K = 20
MMR_TOP_K = 5
MMR_LAMBDA = 0.7
MMR_SCORE_THRESHOLD = 0.01

# History
HISTORY_DIR = BASE_DIR / "conversation_history"
MAX_HISTORY_ROUNDS = 20

# Supported document types
SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx", ".html"]
