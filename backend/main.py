import sys, os, shutil, json
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from backend.config import (
    DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, QWEN_MODEL,
    KNOWLEDGE_BASES_DIR, SUPPORTED_EXTENSIONS, HISTORY_DIR,
)
from backend.loader import list_knowledge_bases, load_documents
from backend.chunker import build_chunks
from backend.embedder import generate_embeddings, save_embeddings
from backend.indexer import build_faiss_index, index_exists
from backend.retriever import mmr_search, clear_kb_cache
from backend.history import session_manager, ChatHistory

app = FastAPI(title="Yuti RAG API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_qwen_client():
    from openai import OpenAI

    if not DASHSCOPE_API_KEY:
        raise HTTPException(status_code=500, detail="DASHSCOPE_API_KEY not configured in .env")
    return OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)


def _ask_qwen(prompt: str) -> str:
    client = _get_qwen_client()
    response = client.chat.completions.create(
        model=QWEN_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _build_prompt(query: str, retrieved: list[dict], history_text: str, kb_name: str = "") -> str:
    context_parts = []
    for i, chunk in enumerate(retrieved, 1):
        context_parts.append(
            f"[Reference {i}]\n"
            f"File: {chunk.get('filename', 'unknown')}\n"
            f"Content:\n{chunk.get('content', '')}\n"
        )
    context = "\n".join(context_parts)

    history_section = ""
    if history_text.strip():
        history_section = f"\n## Conversation History\n{history_text}\n"

    kb_display = KB_DISPLAY_NAMES.get(kb_name, kb_name)
    prompt = f"""You are a knowledge base Q&A assistant specializing in Yunnan's intangible cultural heritage. Current knowledge base: [{kb_display}].

{history_section}
## Reference Context
{context}

## Question
{query}

## Rules
1. Only answer if the question is relevant to the current knowledge base.
2. Base your answer primarily on the reference context provided.
3. You may supplement with your own knowledge, but no more than 30% of the answer.
4. Cite source filenames at the end.
5. Respond in Chinese unless asked otherwise.

Answer:"""
    return prompt


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    knowledge_base: str = Field(...)
    session_id: str = Field(default="default")


class SourceItem(BaseModel):
    filename: str
    source: str
    content: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    session_id: str


class KBInfoResponse(BaseModel):
    name: str
    display_name: str
    document_count: int
    indexed: bool
    chunk_count: int = 0


KB_DISPLAY_NAMES = {
    "dongba": "东巴文化", "puercha": "普洱茶制作技艺", "zharan": "扎染",
    "huobajie": "火把节", "poshuijie": "泼水节", "kongquewu": "孔雀舞",
    "naxiguyue": "纳西古乐", "jianshuizitao": "建水紫陶",
    "wutong": "乌铜走银", "heqingyinqi": "鹤庆银器",
}


@app.get("/api/health")
async def health_check():
    kbs = list_knowledge_bases()
    return {"status": "ok", "version": "1.1.0", "knowledge_bases": len(kbs), "model": QWEN_MODEL}


@app.get("/api/kb/list")
async def get_kb_list():
    kbs = list_knowledge_bases()
    return {
        "knowledge_bases": [
            {"name": n, "display_name": KB_DISPLAY_NAMES.get(n, n), "indexed": index_exists(n)}
            for n in kbs
        ],
        "total": len(kbs),
    }


@app.get("/api/kb/{kb_name}/info")
async def get_kb_info(kb_name: str):
    if kb_name not in list_knowledge_bases():
        raise HTTPException(status_code=404, detail=f"KB [{kb_name}] not found")

    docs = load_documents(kb_name)
    chunk_count = 0
    try:
        from backend.indexer import load_faiss_index
        _, metadata = load_faiss_index(kb_name)
        chunk_count = len(metadata)
    except Exception:
        pass

    return {
        "name": kb_name,
        "display_name": KB_DISPLAY_NAMES.get(kb_name, kb_name),
        "document_count": len(docs),
        "documents": [{"filename": d["filename"], "size": len(d["content"])} for d in docs],
        "indexed": index_exists(kb_name),
        "chunk_count": chunk_count,
    }


@app.post("/api/kb/build")
async def build_knowledge_base(kb_name: str = Query(...)):
    if kb_name not in list_knowledge_bases():
        raise HTTPException(status_code=404, detail=f"KB [{kb_name}] not found")

    try:
        chunks = build_chunks(kb_name)
        if not chunks:
            raise HTTPException(status_code=400, detail="No valid documents in KB")

        embeddings = generate_embeddings(chunks)
        save_embeddings(embeddings, kb_name)
        index, metadata = build_faiss_index(kb_name, embeddings)
        clear_kb_cache(kb_name)

        return {
            "status": "success",
            "knowledge_base": kb_name,
            "chunks": len(chunks),
            "embeddings": len(embeddings),
            "vectors": index.ntotal,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kb/build-all")
async def build_all_knowledge_bases():
    kbs = list_knowledge_bases()
    results, errors = [], []

    for kb_name in kbs:
        try:
            chunks = build_chunks(kb_name)
            if not chunks:
                errors.append({"kb": kb_name, "error": "no documents"})
                continue
            embeddings = generate_embeddings(chunks)
            save_embeddings(embeddings, kb_name)
            index, _ = build_faiss_index(kb_name, embeddings)
            clear_kb_cache(kb_name)
            results.append({"kb": kb_name, "chunks": len(chunks), "vectors": index.ntotal})
        except Exception as e:
            errors.append({"kb": kb_name, "error": str(e)})

    return {"status": "completed", "success": len(results), "failed": len(errors), "results": results, "errors": errors}


class CreateKBRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


@app.post("/api/kb/create")
async def create_knowledge_base(req: CreateKBRequest):
    import re
    if any(c in req.name for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '.', '\n', '\r']):
        raise HTTPException(status_code=400, detail="Invalid KB name: contains illegal characters")

    kb_dir = KNOWLEDGE_BASES_DIR / req.name
    if kb_dir.exists():
        raise HTTPException(status_code=409, detail=f"KB [{req.name}] already exists")

    kb_dir.mkdir(parents=True, exist_ok=False)
    return {"status": "ok", "name": req.name}


@app.delete("/api/kb/{kb_name}")
async def delete_knowledge_base(kb_name: str):
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    if not kb_dir.exists():
        raise HTTPException(status_code=404, detail=f"KB [{kb_name}] not found")

    try:
        shutil.rmtree(kb_dir)
        clear_kb_cache(kb_name)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kb/{kb_name}/upload")
async def upload_documents(kb_name: str, files: list[UploadFile] = File(...), auto_rebuild: bool = Form(True)):
    available = list_knowledge_bases()
    if kb_name not in available:
        raise HTTPException(status_code=404, detail=f"KB [{kb_name}] not found")

    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    uploaded, skipped, errors = [], [], []

    for file in files:
        if not file.filename:
            continue
        suffix = Path(file.filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            skipped.append({"filename": file.filename, "reason": f"unsupported type: {suffix}"})
            continue
        try:
            content = await file.read()
            with open(kb_dir / file.filename, "wb") as f:
                f.write(content)
            uploaded.append({"filename": file.filename, "size": len(content)})
        except Exception as e:
            errors.append({"filename": file.filename, "error": str(e)})

    result = {"status": "ok", "knowledge_base": kb_name, "uploaded": uploaded, "skipped": skipped, "errors": errors}

    if auto_rebuild and uploaded:
        try:
            chunks = build_chunks(kb_name)
            embeddings = generate_embeddings(chunks)
            save_embeddings(embeddings, kb_name)
            index, _ = build_faiss_index(kb_name, embeddings)
            clear_kb_cache(kb_name)
            result["rebuild"] = {"status": "success", "chunks": len(chunks), "vectors": index.ntotal}
        except Exception as e:
            result["rebuild"] = {"status": "failed", "error": str(e)}

    return result


@app.delete("/api/kb/{kb_name}/documents/{filename}")
async def delete_document(kb_name: str, filename: str, auto_rebuild: bool = True):
    available = list_knowledge_bases()
    if kb_name not in available:
        raise HTTPException(status_code=404, detail=f"KB [{kb_name}] not found")

    file_path = KNOWLEDGE_BASES_DIR / kb_name / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Document [{filename}] not found")

    file_path.unlink()
    result = {"status": "ok", "knowledge_base": kb_name, "deleted": filename}

    if auto_rebuild:
        try:
            chunks = build_chunks(kb_name)
            if chunks:
                embeddings = generate_embeddings(chunks)
                save_embeddings(embeddings, kb_name)
                index, _ = build_faiss_index(kb_name, embeddings)
                clear_kb_cache(kb_name)
                result["rebuild"] = {"status": "success", "chunks": len(chunks), "vectors": index.ntotal}
            else:
                result["rebuild"] = {"status": "skipped", "reason": "KB empty after deletion"}
        except Exception as e:
            result["rebuild"] = {"status": "failed", "error": str(e)}

    return result


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    available = list_knowledge_bases()
    if req.knowledge_base not in available:
        raise HTTPException(status_code=404, detail=f"KB [{req.knowledge_base}] not found")

    if not index_exists(req.knowledge_base):
        raise HTTPException(status_code=400, detail=f"KB [{req.knowledge_base}] index not built. Run build first.")

    # Retrieve
    retrieved = mmr_search(req.question, req.knowledge_base)

    is_hit = retrieved[0]["source"] != "__system__" if retrieved else False
    if is_hit and retrieved[0]["score"] < 0.40:
        is_hit = False

    if not is_hit:
        kb_display = KB_DISPLAY_NAMES.get(req.knowledge_base, req.knowledge_base)
        answer = f"Sorry, I couldn't find relevant information in [{kb_display}]. Try switching to another knowledge base."
        session = session_manager.get_session(req.session_id)
        session.add(req.question, {"text": answer, "score": 0.0, "sources": []})
        return ChatResponse(answer=answer, sources=[], session_id=req.session_id)

    session = session_manager.get_session(req.session_id)
    history_text = session.get_history_text(max_rounds=10)
    prompt = _build_prompt(req.question, retrieved, history_text, req.knowledge_base)

    try:
        answer = _ask_qwen(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM call failed: {str(e)}")

    session.add(req.question, {"text": answer, "score": retrieved[0]["score"], "sources": retrieved})

    sources = [
        SourceItem(
            filename=r.get("filename", ""), source=r.get("source", ""),
            content=r.get("content", "")[:300] + "...", score=round(r.get("score", 0), 4),
        )
        for r in retrieved if r.get("source") != "__system__"
    ]

    return ChatResponse(answer=answer, sources=sources, session_id=req.session_id)


@app.get("/api/history")
async def get_history(session_id: str = "default"):
    session = session_manager.get_session(session_id)
    return {"session_id": session_id, "messages": session.get_all(), "total": session.count}


@app.get("/api/history/sessions")
async def list_sessions():
    return {"sessions": session_manager.list_sessions()}


@app.delete("/api/history")
async def clear_history(session_id: str = "default"):
    session = session_manager.get_session(session_id)
    session.clear()
    return {"status": "ok"}


@app.delete("/api/history/sessions/{session_id}")
async def delete_session(session_id: str):
    session_manager.delete_session(session_id)
    return {"status": "ok"}


class FeedbackRequest(BaseModel):
    message_id: str = Field(...)
    type: str = Field(...)


@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    import time
    feedback_dir = HISTORY_DIR / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)

    record = {"message_id": req.message_id, "type": req.type, "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}

    with open(feedback_dir / "feedback.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    print("Yuti RAG API — http://localhost:8001/docs")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8001, reload=True)
