# Yuti RAG

> Multi-knowledge-base RAG QA system for Yunnan's intangible cultural heritage.  
> Built with FAISS vector search, MMR re-ranking, and LLM generation.

## Why

Most RAG demos use a single knowledge base and skip retrieval quality. This project explores the opposite:

- **Multi-KB isolation** — each knowledge base gets its own vector index, metadata store, and search space
- **Diverse retrieval strategy** — FAISS cosine search for recall, MMR re-ranking for precision and diversity
- **Traceable answers** — every response cites source documents with relevance scores
- **Symmetric design** — frontend and backend are independently runnable, communicates over REST

The subject domain (Yunnan ICH) was chosen because the documents are well-structured, domain-specific, and non-trivial for a generic LLM to answer without retrieval.

## Architecture

```
User Question
    │
    ▼
Query Encoding (bge-small-zh-v1.5)
    │
    ▼
FAISS IndexFlatIP (cosine similarity, Top-20)
    │
    ▼
MMR Re-ranking (λ·rel − (1−λ)·div, Top-5)
    │
    ▼
Prompt Construction (context + history + question)
    │
    ▼
Qwen API (temperature=0.3, max_tokens=1024)
    │
    ▼
Answer + Source Citations
```

### Retrieval quality matters

The MMR (Maximal Marginal Relevance) step is the key differentiator. Without it, Top-5 results from FAISS often cluster around a single document. MMR penalizes redundancy:

```python
mmr_score = λ · sim(query, doc_i) − (1−λ) · max sim(doc_i, doc_j)
```

With `λ=0.7`, the pipeline keeps 70% relevance weight while spending 30% on diversity. The `build_index.py` script also allows adjusting chunk size (500 chars) and overlap (100 chars) per knowledge base.

## Project structure

```
backend/
├── main.py          # FastAPI server — all API routes
├── config.py        # shared configuration
├── loader.py        # document loading (txt, pdf, docx, md, html)
├── chunker.py       # text splitting with overlap
├── embedder.py      # sentence-transformers embedding
├── indexer.py       # FAISS index build & load
├── retriever.py     # MMR search logic
├── history.py       # session & conversation persistence
└── build_index.py   # CLI script to build all KB indexes

frontend/
├── src/
│   ├── App.tsx
│   ├── api/index.ts
│   ├── hooks/useChat.ts
│   ├── types/index.ts
│   └── components/
│       ├── Sidebar.tsx, ChatView.tsx, ChatBubble.tsx, ChatInput.tsx
│       ├── KBCapsule.tsx, WelcomePage.tsx, ThemeToggle.tsx
│       └── ...
├── package.json
└── vite.config.ts

knowledge_bases/      # 10 source document collections (tracked)
bge-small-zh-v1.5/    # local embedding model (download separately)
```

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. Set up API key
echo "DASHSCOPE_API_KEY=your-key" > .env

# 3. Build vector indexes
cd backend && python build_index.py

# 4. Start backend (8001) and frontend (5174)
python -m uvicorn backend.main:app --reload --port 8001
cd frontend && npm run dev
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/chat` | Ask a question against a knowledge base |
| GET | `/api/kb/list` | List all knowledge bases |
| GET | `/api/kb/{name}/info` | KB details + document list |
| POST | `/api/kb/build` | Build/rebuild a KB vector index |
| POST | `/api/kb/build-all` | Rebuild all indexes |
| POST | `/api/kb/create` | Create a new empty KB |
| DELETE | `/api/kb/{name}` | Delete a KB and its index |
| POST | `/api/kb/{name}/upload` | Upload documents |
| DELETE | `/api/kb/{name}/documents/{filename}` | Delete a document |
| GET | `/api/history` | List sessions / get history |
| POST | `/api/feedback` | Record thumbs up/down feedback |

## Stack

- **Backend**: Python 3.11, FastAPI, Uvicorn
- **Search**: FAISS (IndexFlatIP), sentence-transformers (bge-small-zh-v1.5)
- **LLM**: Qwen API (OpenAI-compatible)
- **Frontend**: React 18, Vite, TypeScript, TailwindCSS, Framer Motion
- **Document parsing**: PyPDF2, python-docx

## License

MIT
