# ==========================
# 模块 01：FastAPI 主程序
# 功能：RAG 问答系统的所有 API 接口
#       - POST /api/chat       智能问答
#       - GET  /api/kb/list    知识库列表
#       - GET  /api/kb/{name}/info  知识库详情
#       - POST /api/kb/build   构建知识库
#       - GET  /api/history    对话历史
#       - DELETE /api/history  清空历史
#       - GET  /api/health     健康检查
# ==========================
import sys
import os

# 确保 backend 包可导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import shutil
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from typing import Optional

from backend.config import (
    DASHSCOPE_API_KEY,
    DASHSCOPE_BASE_URL,
    QWEN_MODEL,
    KNOWLEDGE_BASES_DIR,
    SUPPORTED_EXTENSIONS,
)
from backend.rag_02_zhishiku_jiazai import list_knowledge_bases, load_documents
from backend.rag_03_wendang_qiefen import build_chunks
from backend.rag_04_xiangliang_bianma import generate_embeddings, save_embeddings
from backend.rag_05_faiss_goujian import build_faiss_index, index_exists
from backend.rag_06_jiansuo_mmr import mmr_search, clear_kb_cache
from backend.rag_07_duihua_jilu import session_manager, ChatHistory

# ══════════════════════════════════════
# FastAPI 应用
# ══════════════════════════════════════
app = FastAPI(
    title="云南非物质文化遗产智能问答系统",
    description="基于 RAG 技术的云南非遗知识库助手",
    version="1.0.0",
)

# CORS：允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════
# OpenAI 兼容客户端（千问 API）
# ══════════════════════════════════════
def _get_qwen_client():
    """获取千问 API 客户端"""
    from openai import OpenAI

    if not DASHSCOPE_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="API Key 未配置，请在 .env 文件中设置 DASHSCOPE_API_KEY",
        )
    return OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)


def _ask_qwen(prompt: str) -> str:
    """调用千问 API 生成回答"""
    client = _get_qwen_client()
    response = client.chat.completions.create(
        model=QWEN_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _build_prompt(query: str, retrieved: list[dict], history_text: str, kb_name: str = "") -> str:
    """构建 RAG Prompt"""
    # 拼接参考上下文
    context_parts = []
    for i, chunk in enumerate(retrieved, 1):
        context_parts.append(
            f"【参考资料 {i}】\n"
            f"来源文件: {chunk.get('filename', '未知')}\n"
            f"内容:\n{chunk.get('content', '')}\n"
        )
    context = "\n".join(context_parts)

    # 历史对话
    history_section = ""
    if history_text.strip():
        history_section = f"\n## 历史对话\n{history_text}\n"

    kb_display = KB_DISPLAY_NAMES.get(kb_name, kb_name)
    prompt = f"""你是一位云南非物质文化遗产知识库问答助手。你当前的知识库是【{kb_display}】。

{history_section}
## 参考资料
{context}

## 用户问题
{query}

## 回答规则
1. **用户的问题必须与当前知识库主题相关**才回答。如果用户问的内容明显不属于当前知识库（例如在普洱茶知识库问扎染），请直接回复："抱歉，当前知识库中没有相关信息，我无法回答这个问题。请切换到对应知识库试试。"
2. **以参考资料为核心**：回答的主体信息必须来自参考资料
3. **可少量补充**：参考资料中缺少的细节可以用你自身知识补充，但补充内容不超过回答的30%
4. 回答要**结构清晰**、**自然流畅**
5. 在回答末尾列出**参考来源**（文件名）

请回答："""

    return prompt


# ══════════════════════════════════════
# 请求/响应模型
# ══════════════════════════════════════
class ChatRequest(BaseModel):
    question: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    knowledge_base: str = Field(..., description="知识库名称")
    session_id: str = Field(default="default", description="会话ID")


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


# ══════════════════════════════════════
# KB 名称映射（拼音 → 中文）
# ══════════════════════════════════════
KB_DISPLAY_NAMES = {
    "dongba": "东巴文化",
    "puercha": "普洱茶制作技艺",
    "zharan": "扎染",
    "huobajie": "火把节",
    "poshuijie": "泼水节",
    "kongquewu": "孔雀舞",
    "naxiguyue": "纳西古乐",
    "jianshuizitao": "建水紫陶",
    "wutong": "乌铜走银",
    "heqingyinqi": "鹤庆银器",
}


# ══════════════════════════════════════
# API 路由
# ══════════════════════════════════════
@app.get("/api/health")
async def health_check():
    """健康检查"""
    kbs = list_knowledge_bases()
    return {
        "status": "ok",
        "version": "1.0.0",
        "knowledge_bases": len(kbs),
        "model": QWEN_MODEL,
    }


@app.get("/api/kb/list")
async def get_kb_list():
    """获取所有知识库列表"""
    kbs = list_knowledge_bases()
    result = []
    for name in kbs:
        result.append({
            "name": name,
            "display_name": KB_DISPLAY_NAMES.get(name, name),
            "indexed": index_exists(name),
        })
    return {"knowledge_bases": result, "total": len(result)}


@app.get("/api/kb/{kb_name}/info")
async def get_kb_info(kb_name: str):
    """获取单个知识库详情"""
    if kb_name not in list_knowledge_bases():
        raise HTTPException(status_code=404, detail=f"知识库 [{kb_name}] 不存在")

    docs = load_documents(kb_name)

    # 尝试获取 chunk 数量
    chunk_count = 0
    try:
        from backend.rag_05_faiss_goujian import load_faiss_index
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
async def build_knowledge_base(kb_name: str):
    """为指定知识库构建 embedding 和 FAISS 索引"""
    if kb_name not in list_knowledge_bases():
        raise HTTPException(status_code=404, detail=f"知识库 [{kb_name}] 不存在")

    try:
        # 1. 加载 & 切分
        chunks = build_chunks(kb_name)
        if not chunks:
            raise HTTPException(status_code=400, detail="知识库无有效文档")

        # 2. Embedding
        embeddings = generate_embeddings(chunks)
        save_embeddings(embeddings, kb_name)

        # 3. FAISS 索引
        index, metadata = build_faiss_index(kb_name, embeddings)

        # 4. 清除旧缓存
        clear_kb_cache(kb_name)

        return {
            "status": "success",
            "knowledge_base": kb_name,
            "chunks": len(chunks),
            "embeddings": len(embeddings),
            "vectors": index.ntotal,
            "message": f"知识库 [{kb_name}] 构建完成",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/kb/build-all")
async def build_all_knowledge_bases():
    """一键构建所有知识库"""
    kbs = list_knowledge_bases()
    results = []
    errors = []

    for kb_name in kbs:
        try:
            chunks = build_chunks(kb_name)
            if not chunks:
                errors.append({"kb": kb_name, "error": "无有效文档"})
                continue
            embeddings = generate_embeddings(chunks)
            save_embeddings(embeddings, kb_name)
            index, _ = build_faiss_index(kb_name, embeddings)
            clear_kb_cache(kb_name)
            results.append({
                "kb": kb_name,
                "chunks": len(chunks),
                "vectors": index.ntotal,
            })
        except Exception as e:
            errors.append({"kb": kb_name, "error": str(e)})

    return {
        "status": "completed",
        "success": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


# ══════════════════════════════════════
# 知识库 CRUD
# ══════════════════════════════════════

class CreateKBRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)


@app.post("/api/kb/create")
async def create_knowledge_base(req: CreateKBRequest):
    """创建新知识库（空目录）"""
    # 允许中文/英文/数字/下划线/连字符/空格
    import re
    # 排除路径分隔符等危险字符即可
    if not req.name or any(c in req.name for c in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '.', '\n', '\r']):
        raise HTTPException(status_code=400, detail="名称包含非法字符")

    kb_dir = KNOWLEDGE_BASES_DIR / req.name
    if kb_dir.exists():
        raise HTTPException(status_code=409, detail=f"知识库 [{req.name}] 已存在")

    kb_dir.mkdir(parents=True, exist_ok=False)
    return {"status": "ok", "name": req.name, "message": f"知识库 [{req.name}] 创建成功"}


@app.delete("/api/kb/{kb_name}")
async def delete_knowledge_base(kb_name: str):
    """删除整个知识库（包括所有文件和索引）"""
    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    if not kb_dir.exists():
        raise HTTPException(status_code=404, detail=f"知识库 [{kb_name}] 不存在")

    try:
        shutil.rmtree(kb_dir)
        clear_kb_cache(kb_name)
        return {"status": "ok", "message": f"知识库 [{kb_name}] 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")


# ══════════════════════════════════════
# 文档上传 / 删除 / 重建
# ══════════════════════════════════════

@app.post("/api/kb/{kb_name}/upload")
async def upload_documents(
    kb_name: str,
    files: list[UploadFile] = File(..., description="文档文件 (TXT/PDF/DOCX/MD/HTML)"),
    auto_rebuild: bool = Form(default=True, description="上传后自动重建索引"),
):
    """
    上传文档到指定知识库
    - 支持多文件同时上传
    - 自动过滤不支持的文件类型
    - 可选自动重建索引
    """
    available = list_knowledge_bases()
    if kb_name not in available:
        raise HTTPException(
            status_code=404,
            detail=f"知识库 [{kb_name}] 不存在。可用: {available}",
        )

    kb_dir = KNOWLEDGE_BASES_DIR / kb_name
    kb_dir.mkdir(parents=True, exist_ok=True)

    uploaded = []
    skipped = []
    errors = []

    for file in files:
        if not file.filename:
            continue

        suffix = Path(file.filename).suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            skipped.append({
                "filename": file.filename,
                "reason": f"不支持的文件类型: {suffix}",
            })
            continue

        try:
            content = await file.read()
            save_path = kb_dir / file.filename
            with open(save_path, "wb") as f:
                f.write(content)
            uploaded.append({
                "filename": file.filename,
                "size": len(content),
            })
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e),
            })

    result = {
        "status": "ok",
        "knowledge_base": kb_name,
        "uploaded": uploaded,
        "uploaded_count": len(uploaded),
        "skipped": skipped,
        "errors": errors,
    }

    # 自动重建索引
    if auto_rebuild and uploaded:
        try:
            chunks = build_chunks(kb_name)
            embeddings = generate_embeddings(chunks)
            save_embeddings(embeddings, kb_name)
            index, meta = build_faiss_index(kb_name, embeddings)
            clear_kb_cache(kb_name)
            result["rebuild"] = {
                "status": "success",
                "chunks": len(chunks),
                "vectors": index.ntotal,
            }
        except Exception as e:
            result["rebuild"] = {
                "status": "failed",
                "error": str(e),
            }

    return result


@app.delete("/api/kb/{kb_name}/documents/{filename}")
async def delete_document(
    kb_name: str,
    filename: str,
    auto_rebuild: bool = True,
):
    """
    删除知识库中指定文档，可选自动重建索引
    """
    available = list_knowledge_bases()
    if kb_name not in available:
        raise HTTPException(status_code=404, detail=f"知识库 [{kb_name}] 不存在")

    file_path = KNOWLEDGE_BASES_DIR / kb_name / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文档 [{filename}] 不存在")

    try:
        file_path.unlink()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {e}")

    result = {
        "status": "ok",
        "knowledge_base": kb_name,
        "deleted": filename,
    }

    # 自动重建
    if auto_rebuild:
        try:
            chunks = build_chunks(kb_name)
            if chunks:
                embeddings = generate_embeddings(chunks)
                save_embeddings(embeddings, kb_name)
                index, meta = build_faiss_index(kb_name, embeddings)
                clear_kb_cache(kb_name)
                result["rebuild"] = {
                    "status": "success",
                    "chunks": len(chunks),
                    "vectors": index.ntotal,
                }
            else:
                result["rebuild"] = {
                    "status": "skipped",
                    "reason": "知识库已无文档",
                }
        except Exception as e:
            result["rebuild"] = {
                "status": "failed",
                "error": str(e),
            }

    return result


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    核心智能问答接口

    RAG 流程：
    1. 编码问题
    2. FAISS 召回 Top-20
    3. MMR 重排序 Top-5
    4. 构建 Prompt
    5. 千问生成答案
    6. 保存历史 & 返回
    """
    # 验证知识库
    available = list_knowledge_bases()
    if req.knowledge_base not in available:
        raise HTTPException(
            status_code=404,
            detail=f"知识库 [{req.knowledge_base}] 不存在。可用: {available}",
        )

    # 检查索引是否已构建
    if not index_exists(req.knowledge_base):
        raise HTTPException(
            status_code=400,
            detail=f"知识库 [{req.knowledge_base}] 尚未构建索引。请先在管理面板点击「构建知识库」。",
        )

    # ── RAG 流程 ──
    # 1+2+3. 检索
    retrieved = mmr_search(req.question, req.knowledge_base)

    # 判断是否命中（第一个结果是否来自实际文档，且分数足够高）
    is_hit = retrieved[0]["source"] != "系统" if retrieved else False
    # 分数低于 0.40 视为低质量命中（跨库噪声），拒绝
    if is_hit and retrieved[0]["score"] < 0.40:
        is_hit = False

    # 未命中 → 直接拒绝
    if not is_hit:
        kb_display = KB_DISPLAY_NAMES.get(req.knowledge_base, req.knowledge_base)
        answer = f"抱歉，我无法回答这个问题。\n\n当前知识库为【{kb_display}】，库中没有找到与您问题相关的内容。请切换到其他知识库或换个问题试试。"
        session = session_manager.get_session(req.session_id)
        session.add(req.question, {"text": answer, "score": 0.0, "sources": []})
        return ChatResponse(
            answer=answer,
            sources=[],
            session_id=req.session_id,
        )

    # 4. 获取对话历史
    session = session_manager.get_session(req.session_id)
    history_text = session.get_history_text(max_rounds=10)

    # 5. 构建 Prompt
    prompt = _build_prompt(req.question, retrieved, history_text, req.knowledge_base)

    # 6. 调用千问
    try:
        answer = _ask_qwen(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"大模型调用失败: {str(e)}")

    # 7. 保存历史
    session.add(req.question, {
        "text": answer,
        "score": retrieved[0]["score"] if is_hit else 0.0,
        "sources": retrieved if is_hit else [],
    })

    # 8. 组装来源
    sources = []
    for r in retrieved:
        if r.get("source") != "系统":
            sources.append(SourceItem(
                filename=r.get("filename", ""),
                source=r.get("source", ""),
                content=r.get("content", "")[:300] + "...",
                score=round(r.get("score", 0), 4),
            ))

    return ChatResponse(
        answer=answer,
        sources=sources,
        session_id=req.session_id,
    )


@app.get("/api/history")
async def get_history(session_id: str = "default"):
    """获取对话历史"""
    session = session_manager.get_session(session_id)
    return {
        "session_id": session_id,
        "messages": session.get_all(),
        "total": session.count,
    }


@app.get("/api/history/sessions")
async def list_sessions():
    """列出所有会话"""
    return {"sessions": session_manager.list_sessions()}


@app.delete("/api/history")
async def clear_history(session_id: str = "default"):
    """清空指定会话的历史"""
    session = session_manager.get_session(session_id)
    session.clear()
    return {"status": "ok", "message": f"会话 [{session_id}] 历史已清空"}


@app.delete("/api/history/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除指定会话"""
    session_manager.delete_session(session_id)
    return {"status": "ok", "message": f"会话 [{session_id}] 已删除"}


# ══════════════════════════════════════
# 用户反馈
# ══════════════════════════════════════

class FeedbackRequest(BaseModel):
    message_id: str = Field(..., description="消息ID")
    type: str = Field(..., description="反馈类型: like / dislike")


@app.post("/api/feedback")
async def submit_feedback(req: FeedbackRequest):
    """记录用户对AI回答的反馈"""
    import time
    feedback_dir = HISTORY_DIR / "feedback"
    feedback_dir.mkdir(parents=True, exist_ok=True)

    record = {
        "message_id": req.message_id,
        "type": req.type,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # 追加到 JSONL 文件
    file_path = feedback_dir / "feedback.jsonl"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"status": "ok", "message": "反馈已记录"}


# ══════════════════════════════════════
# 启动入口
# ══════════════════════════════════════
if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("  云南非物质文化遗产智能问答系统 (RAG)")
    print("  API 文档: http://localhost:8001/docs")
    print("=" * 60)

    uvicorn.run(
        "backend.rag_01_app:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )
