<div align="center">

# Yuti RAG

**Multi-Knowledge-Base RAG QA System for Yunnan's Intangible Cultural Heritage**
FAISS vector search + MMR re-ranking + LLM generation.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## Overview

Yuti RAG answers questions about Yunnan's intangible cultural heritage across **10 isolated knowledge bases** (Dongba hieroglyphs, Pu'er tea, tie-dye, Torch Festival, etc.). Each KB maintains its own FAISS vector index, ensuring domain-precise retrieval.

The key differentiator is **MMR (Maximum Marginal Relevance) re-ranking** — instead of returning the top-5 most-similar chunks (which often cluster around one document), MMR balances relevance with diversity so answers draw from multiple sources.

```
Question → Embed (bge-small-zh-v1.5) → FAISS Top-20 → MMR λ=0.7 Top-5 → LLM (Qwen) → Answer + Sources
```

## Features

- **Multi-KB isolation** — Each knowledge base has its own FAISS index, metadata, and search scope
- **MMR re-ranking** — `MMR = λ·sim(q,d) − (1−λ)·max sim(d_i,d_j)` reduces redundancy in retrieved chunks
- **Traceable answers** — Every response cites source documents with relevance scores
- **Full KB lifecycle management** — Create, upload, search, delete via UI or REST API
- **Persistent sessions** — Conversation history with 20-round context window
- **Modern UI** — React 18 + TypeScript + TailwindCSS + Framer Motion, dark/light themes

## Quick Start

```bash
# Install
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Configure + build index
cp .env.example .env    # set DASHSCOPE_API_KEY
cd backend && python build_index.py && cd ..

# Start (two terminals)
python -m uvicorn backend.main:app --reload --port 8001
cd frontend && npm run dev
```

Open http://localhost:5174

### Docker

```bash
cp .env.example .env
docker compose up -d
```

## Evaluation

| Metric | Value |
|--------|-------|
| Embedding dimension | 512 (BAAI/bge-small-zh-v1.5) |
| Chunk size / overlap | 500 / 100 chars |
| FAISS coarse search | Top-20 (IndexFlatIP, cosine similarity) |
| MMR re-rank | Top-5 (λ=0.7) |
| Recall fallback | Score < 0.40 → "no relevant info" |
| Test suite | 42 passing tests |

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Ask a question against a knowledge base |
| GET | `/api/kb/list` | List all knowledge bases |
| GET | `/api/kb/{name}/info` | KB details + document list |
| POST | `/api/kb/build` | Build/rebuild a KB vector index |
| POST | `/api/kb/{name}/upload` | Upload documents |
| DELETE | `/api/kb/{name}` / `.../documents/{file}` | Delete KB or document |
| GET | `/api/history` | Get conversation history |
| POST | `/api/feedback` | Record thumbs up/down |

Interactive docs at http://localhost:8001/docs

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, Uvicorn |
| Search | FAISS (IndexFlatIP), sentence-transformers |
| LLM | Qwen API (OpenAI-compatible) |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Framer Motion |
| Documents | PyPDF2, python-docx |
| Testing | pytest (42 tests) |
| Deployment | Docker, docker-compose |

## License

MIT — see [LICENSE](LICENSE).
