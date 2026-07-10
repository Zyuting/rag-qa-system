<div align="center">

# Domain Knowledge Assistant Based on Retrieval-Augmented Generation (RAG)

**End-to-end RAG pipeline** — Designed and implemented a complete knowledge assistant system for question answering over private domain knowledge bases. Built with FAISS vector search, MMR re-ranking, and LLM-based generation.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

</div>

---

## Overview

This project demonstrates a complete **Retrieval-Augmented Generation (RAG)** system that enables LLM-based question answering over private knowledge bases. It implements the full pipeline — from document preprocessing and vector indexing to semantic retrieval and LLM-powered response generation.

The system manages **10 isolated knowledge bases** in the domain of intangible cultural heritage. Each KB maintains its own FAISS vector index with MMR (Maximum Marginal Relevance) re-ranking, ensuring diverse and grounded answers across domain-specific sources.

```
User Query → Embedding (bge-small-zh-v1.5) → FAISS Top-20 Retrieval → MMR λ=0.7 Re-rank → Top-5 Context → LLM (Qwen) → Grounded Answer + Source Citations
```

## Architecture & Pipeline

### RAG Pipeline

- **Document Preprocessing** — Handles PDF, DOCX, and text files with automatic chunking (500 chars, 100-char overlap)
- **Embedding Generation** — Uses sentence-transformers (bge-small-zh-v1.5) to encode document chunks into 512-dim vectors
- **Vector Storage & Retrieval** — FAISS IndexFlatIP with cosine similarity for fast approximate nearest neighbor search
- **MMR Re-ranking** — Balances relevance and diversity in retrieved chunks: `MMR = λ·sim(q,d) − (1−λ)·max sim(d_i,d_j)`
- **LLM Response Generation** — Integrates OpenAI-compatible LLM APIs with structured prompt templates
- **Recall Fallback** — Automatically detects low-confidence retrievals (score < 0.40) and returns "no relevant information"

### Key Features

- **Designed a complete RAG pipeline** — Document preprocessing → chunking → embedding → vector retrieval → LLM-based response generation
- **Implemented semantic search** with FAISS vector database to improve knowledge retrieval accuracy
- **Optimized prompt templates and context construction** strategies to reduce hallucination and improve answer grounding
- **Integrated LLM APIs** to build an interactive knowledge assistant for domain-specific question answering
- **MMR re-ranking** to balance relevance and diversity in retrieved information
- **Full KB lifecycle management** — Create, upload, search, delete via UI or REST API
- **Persistent sessions** with 20-round conversation history window
- **Modern web interface** — React 18 + TypeScript + TailwindCSS, supporting dark/light themes

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# Configure
cp .env.example .env    # set your LLM API key

# Build vector index
cd backend && python build_index.py && cd ..

# Start services (two terminals)
python -m uvicorn backend.main:app --reload --port 8001
cd frontend && npm run dev
```

Open http://localhost:5174

### Docker Deployment

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
| Recall fallback threshold | Score < 0.40 |
| Test coverage | 42 passing tests |

## API Endpoints

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

Interactive API docs at http://localhost:8001/docs

## Tech Stack

| Layer | Technology |
|-------|-----------|
| LLM Application | RAG Pipeline, Prompt Engineering, LLM API Integration |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Vector Database | FAISS (IndexFlatIP) |
| Embedding | sentence-transformers (bge-small-zh-v1.5) |
| LLM Provider | Qwen API (OpenAI-compatible) |
| Frontend | React 18, TypeScript, Vite, TailwindCSS, Framer Motion |
| Document Processing | PyPDF2, python-docx |
| Testing | pytest (42 tests) |
| Deployment | Docker, docker-compose |

## Keywords

`RAG` `LLM` `Embedding` `Vector Database` `FAISS` `Semantic Search` `Prompt Engineering` `Knowledge Assistant` `Retrieval-Augmented Generation` `LLM Application`

## License

MIT — see [LICENSE](LICENSE).
