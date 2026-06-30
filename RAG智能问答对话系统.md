# RAG 智能问答对话系统 — 云南非物质文化遗产助手

> 基于 **RAG (Retrieval-Augmented Generation)** 技术的云南非遗知识库智能问答系统，支持多知识库隔离、向量检索、MMR 重排序、对话历史管理、来源追溯等核心功能。

---

## 目录

1. [系统概述](#1-系统概述)
2. [技术栈](#2-技术栈)
3. [项目结构](#3-项目结构)
4. [核心架构：RAG 流水线](#4-核心架构rag-流水线)
5. [后端模块详解](#5-后端模块详解)
   - [5.1 全局配置 (config.py)](#51-全局配置-configpy)
   - [5.2 文档加载 (rag_02_zhishiku_jiazai.py)](#52-文档加载-rag_02_zhishiku_jiazaipy)
   - [5.3 文档切分 (rag_03_wendang_qiefen.py)](#53-文档切分-rag_03_wendang_qiefenpy)
   - [5.4 向量编码 (rag_04_xiangliang_bianma.py)](#54-向量编码-rag_04_xiangliang_bianmapy)
   - [5.5 FAISS 索引构建 (rag_05_faiss_goujian.py)](#55-faiss-索引构建-rag_05_faiss_goujianpy)
   - [5.6 MMR 检索 (rag_06_jiansuo_mmr.py)](#56-mmr-检索-rag_06_jiansuo_mmrpy)
   - [5.7 对话历史 (rag_07_duihua_jilu.py)](#57-对话历史-rag_07_duihua_jilupy)
   - [5.8 FastAPI 主程序 (rag_01_app.py)](#58-fastapi-主程序-rag_01_apppy)
   - [5.9 知识库构建脚本 (build_kb.py)](#59-知识库构建脚本-build_kbpy)
6. [前端架构](#6-前端架构)
   - [6.1 API 层 (api/index.ts)](#61-api-层-apiindexts)
   - [6.2 状态管理 (hooks/useChat.ts)](#62-状态管理-hooksusechatts)
   - [6.3 类型定义 (types/index.ts)](#63-类型定义-typesindexts)
   - [6.4 组件体系](#64-组件体系)
7. [RAG 检索细节](#7-rag-检索细节)
   - [7.1 向量编码细节](#71-向量编码细节)
   - [7.2 MMR 重排序算法](#72-mmr-重排序算法)
   - [7.3 Prompt 构建策略](#73-prompt-构建策略)
8. [知识库管理](#8-知识库管理)
9. [API 接口列表](#9-api-接口列表)
10. [环境配置](#10-环境配置)
11. [启动与部署](#11-启动与部署)

---

## 1. 系统概述

本项目是一个面向**云南非物质文化遗产**领域的 RAG 智能问答系统。用户可以选择不同的非遗知识库（如东巴文化、普洱茶、扎染等），系统通过向量检索从对应知识库中召回相关文档片段，再交由大模型（阿里千问 Qwen）生成回答。

**核心特点：**

- **多知识库隔离**：11 个非遗主题知识库独立存储和管理
- **向量检索 + MMR 重排序**：FAISS 粗排 + MMR 精细重排，平衡相关性与多样性
- **来源追溯**：每个回答可追溯到原始文档片段
- **多会话管理**：支持多个对话会话的创建、切换、删除
- **全链路中文支持**：Embedding 模型采用 BAAI/bge-small-zh-v1.5，专为中文优化

---

## 2. 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 后端框架 | **Python 3.11 + FastAPI + Uvicorn** | REST API 服务 |
| 向量检索 | **FAISS (CPU)** | 余弦相似度向量索引 |
| Embedding | **BAAI/bge-small-zh-v1.5** (384维) | 中文文本向量编码 |
| 大模型 | **阿里千问 Qwen** (OpenAI 兼容 API) | 基于检索结果生成回答 |
| 前端框架 | **React 18 + TypeScript + Vite** | 单页应用 UI |
| 样式方案 | **TailwindCSS + Framer Motion** | 毛玻璃设计语言 |
| 文档解析 | **PyPDF2 + python-docx** | PDF/Word 文档读取 |
| 存储 | **JSON 文件 + FAISS 索引文件** | 知识库与对话持久化 |

---

## 3. 项目结构

```
pythonProject/
├── .env                          # API Key 配置（不提交 Git）
├── .env.example                  # 配置示例
├── requirements.txt              # Python 依赖
├── README.md                     # 项目文档
├── start.bat                     # Windows 一键启动脚本
├── run.py                        # 后端启动入口（带路径配置）
├──
├── backend/                      # 后端模块（RAG 核心逻辑）
├──   ├── config.py              # ⭐ 全局配置：路径、参数、环境变量
├──   ├── rag_01_app.py          # ⭐ FastAPI 主程序：所有 API 路由
├──   ├── rag_02_zhishiku_jiazai.py  # ⭐ 知识库文档加载（TXT/PDF/DOCX/MD/HTML）
├──   ├── rag_03_wendang_qiefen.py   # ⭐ 文本智能切分（chunk）
├──   ├── rag_04_xiangliang_bianma.py # ⭐ Embedding 向量编码
├──   ├── rag_05_faiss_goujian.py    # ⭐ FAISS 索引构建与加载
├──   ├── rag_06_jiansuo_mmr.py      # ⭐ MMR 重排序检索
├──   ├── rag_07_duihua_jilu.py      # ⭐ 对话历史管理
├──   ├── build_kb.py              # 批量构建所有知识库索引
├──   ├── __init__.py
├──
├── frontend/                     # 前端项目（React + Vite）
├──   ├── package.json
├──   ├── vite.config.ts
├──   ├── index.html
├──   ├── tailwind.config.js
├──   ├── postcss.config.js
├──   ├── tsconfig.json / tsconfig.app.json
├──   ├── src/
├──       ├── main.tsx               # 入口
├──       ├── App.tsx                 # ⭐ 主布局（三栏结构）
├──       ├── index.css               # ⭐ 全局样式 + 毛玻璃设计系统
├──       ├── api/index.ts             # ⭐ 后端 API 调用封装
├──       ├── hooks/useChat.ts         # ⭐ 核心状态管理
├──       ├── types/index.ts           # TypeScript 类型定义
├──       ├── components/
├──           ├── Sidebar.tsx            # 左侧栏（知识库 + 会话列表）
├──           ├── Header.tsx             # 顶部导航
├──           ├── ChatView.tsx            # 聊天主视图
├──           ├── ChatBubble.tsx          # 聊天气泡（含来源面板）
├──           ├── ChatInput.tsx           # 输入框
├──           ├── WelcomePage.tsx         # 首页欢迎页
├──           ├── KBCapsule.tsx           # 知识库胶囊标签
├──           ├── ThemeToggle.tsx          # 深色模式切换
├──
├── knowledge_bases/              # 11 个非遗知识库数据
├──   ├── dongba/                  # 东巴文化（5 文档）
├──   ├── puercha/                 # 普洱茶制作技艺
├──   ├── zharan/                  # 扎染
├──   ├── huobajie/                # 火把节
├──   ├── poshuijie/               # 泼水节
├──   ├── kongquewu/               # 孔雀舞
├──   ├── naxiguyue/               # 纳西古乐
├──   ├── jianshuizitao/           # 建水紫陶
├──   ├── wutong/                  # 乌铜走银
├──   ├── heqingyinqi/             # 鹤庆银器
├──   ├── 福州/                     # 福建福州
├──
├── bge-small-zh-v1.5/            # Embedding 模型文件
├── conversation_history/         # 对话历史持久化 JSON
├── .claude/                      # Claude Code 配置
├── .vscode/                      # VS Code 配置
```

每个知识库目录内包含：

| 文件 | 说明 |
|------|------|
| `*.txt` 等 | 原始文档（知识源） |
| `chunks.txt` | 切分后的文本块（可读） |
| `chunk_embeddings.json` | 向量编码结果（JSON 序列化） |
| `faiss_index.index` | FAISS 向量索引（二进制） |
| `faiss_metadata.json` | 索引元数据（含原始 embedding） |

---

## 4. 核心架构：RAG 流水线

```
┌───────────────────────────────────────────────────────────────────┐
│               第一阶段：知识库构建（离线）              │
│                                                   │
│  原始文档 → 切分(Chunk) → Embedding → FAISS索引  │
│                                                   │
└───────────────────────────────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────┐
│               第二阶段：在线检索 + 生成              │
│                                                   │
│  用户问题 → Embedding → FAISS粗排(Top-20)    │
│                          ↓                           │
│                    MMR重排序(Top-5)                │
│                          ↓                           │
│              构建 Prompt(参考 + 历史)           │
│                          ↓                           │
│                   Qwen API 生成回答               │
│                          ↓                           │
│              返回回答 + 来源追溯               │
└─────────────────────────────────────────────────────┘
```

### 关键数据流

1. **离线阶段**（`build_kb.py`）：原始文档 → 段落切分(500字符/chunk) → bge-small-zh 编码(384维向量) → FAISS 索引存储
2. **在线阶段**（`rag_01_app.py /api/chat`）：
   - 用户问题经同一模型编码
   - FAISS 余弦相似度检索 Top-20
   - MMR 算法重排序 Top-5（平衡相关性与多样性）
   - 相似度分数低于 0.40 时拒绝回答
   - 构建 Prompt → 调用 Qwen API → 返回答案与来源

---

## 5. 后端模块详解

### 5.1 全局配置 (config.py)

> **文件**: [backend/config.py](backend/config.py)

全局配置管理所有可调参数，通过 `python-dotenv` 加载 `.env` 文件：

```python
# ==========================
# 全局配置
# ==========================
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ── API 密钥 ──
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")     # 千问 API Key
DASHSCOPE_BASE_URL = os.getenv("DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1")    # API 地址
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")        # 模型名

# ── 路径 ──
KNOWLEDGE_BASES_DIR = BASE_DIR / "knowledge_bases"         # 知识库根目录
EMBEDDING_MODEL_PATH = str(BASE_DIR / "bge-small-zh-v1.5") # 本地模型路径

# ── 文件名常量 ──
CHUNKS_FILE = "chunks.txt"                  # 切分结果
EMBEDDINGS_FILE = "chunk_embeddings.json"    # 向量数据
INDEX_FILE = "faiss_index.index"             # FAISS 索引
METADATA_FILE = "faiss_metadata.json"        # 索引元数据

# ── 切分参数 ──
CHUNK_SIZE = 500          # 每个 chunk 字符数
CHUNK_OVERLAP = 100       # chunk 重叠字符数
BATCH_SIZE = 16           # Embedding 批处理大小

# ── 检索参数 ──
MMR_FETCH_K = 20          # FAISS 粗排召回数
MMR_TOP_K = 5             # MMR 最终返回数
MMR_LAMBDA = 0.7          # MMR 权衡参数（越大越偏相关性）
MMR_SCORE_THRESHOLD = 0.01  # 最低相似度阈值

# ── 对话历史 ──
HISTORY_DIR = BASE_DIR / "conversation_history"
MAX_HISTORY_ROUNDS = 20   # 最大保留轮次

# ── 支持文档类型 ──
SUPPORTED_EXTENSIONS = [".txt", ".md", ".pdf", ".docx", ".html"]
```

**关键参数说明：**

| 参数 | 默认值 | 作用 |
|------|--------|------|
| `CHUNK_SIZE` | 500 | 每个文本块的目标字符数 |
| `CHUNK_OVERLAP` | 100 | 相邻 chunk 的重叠部分，保证边界语义不丢失 |
| `MMR_FETCH_K` | 20 | FAISS 初次检索数量 |
| `MMR_TOP_K` | 5 | 最终返回数量 |
| `MMR_LAMBDA` | 0.7 | 0.7 偏向相关性，0.3 偏向多样性 |
| `BATCH_SIZE` | 16 | 向量编码的批处理大小 |

---

### 5.2 文档加载 (rag_02_zhishiku_jiazai.py)

> **文件**: [backend/rag_02_zhishiku_jiazai.py](backend/rag_02_zhishiku_jiazai.py)

负责从知识库目录加载文档内容，支持多种文件格式：

**核心函数：**

| 函数 | 作用 |
|------|------|
| `list_knowledge_bases()` | 扫描 `knowledge_bases/` 目录，返回所有知识库名称列表 |
| `load_documents(kb_name)` | 加载指定知识库的全部文档，返回 `[{content, source, filename}]` |

**文件读取器：**

每个格式有独立读取函数，通过映射表统一调用：

```python
_READERS = {
    ".txt": _read_txt,      # UTF-8/GBK/GB2312 自动探测
    ".md": _read_md,        # 同 TXT 读取
    ".html": _read_html,    # 去标签后提取纯文本
    ".pdf": _read_pdf,      # 使用 PyPDF2
    ".docx": _read_docx,    # 使用 python-docx
}
```

**TXT 读取特点：** 自动尝试 `utf-8 → gbk → gb2312 → latin-1` 四种编码，确保中文文档不乱码。

**HTML 读取特点：** 使用正则去除 `<script>`、`<style>` 标签和所有 HTML 标签，保留纯文本内容。

---

### 5.3 文档切分 (rag_03_wendang_qiefen.py)

> **文件**: [backend/rag_03_wendang_qiefen.py](backend/rag_03_wendang_qiefen.py)

将长文档智能切分为固定大小的文本块（chunk），**以段落为单位**保持语义完整：

**切分策略：**

```
┌──────────────────────────────────────────┐
│  文档文本                          │
│    ↓                                 │
│  按 \n 拆分为段落列表                  │
│    ↓                                 │
│  遍历段落                          │
│    ├── 段落超长(>500)→ 滑动窗口切分        │
│    └── 正常段落 → 拼接到当前 chunk          │
│        ↓                             │
│      满 500字 → 保存 chunk                  │
│        ↓                             │
│      新 chunk 从上一个的末尾              │
│      100字重叠开始                     │
└──────────────────────────────────────────┘
```

**关键细节：**

- **段落边界优先**：不会在一个段落中间强制截断，确保语义完整
- **超长段落滑动窗口**：超过 `chunk_size` 的段落，用 `step = chunk_size - chunk_overlap` 的滑动窗口切分
- **chunk 重叠**：相邻 chunk 保留 `chunk_overlap`（100 字符）的重叠，避免边界信息丢失
- **输出**：同时返回 Python 对象和保存可读的 `chunks.txt` 文件

**核心函数：**

| 函数 | 作用 |
|------|------|
| `split_documents(docs)` | 切分文档列表为 chunk 列表 |
| `save_chunks_to_file(chunks, kb_name)` | 将 chunks 保存为可读文本文件 |
| `build_chunks(kb_name)` | 完整流程：加载 → 切分 → 保存 |
| `build_all_chunks()` | 批量构建所有知识库的 chunks |

---

### 5.4 向量编码 (rag_04_xiangliang_bianma.py)

> **文件**: [backend/rag_04_xiangliang_bianma.py](backend/rag_04_xiangliang_bianma.py)

使用 **BAAI/bge-small-zh-v1.5** 模型将文本转换为 384 维向量：

**模型特点：**

- 输出 384 维向量
- 专为中文语义匹配优化
- 支持批量编码（默认 batch_size=16）
- 本地加载，无需联网

**核心函数：**

| 函数 | 作用 |
|------|------|
| `generate_embeddings(chunks)` | 批量编码 chunk 列表 |
| `save_embeddings(embeddings, kb_name)` | 保存为 JSON（紧凑格式，去空格） |
| `load_embeddings(kb_name)` | 从 JSON 加载已有 embedding |
| `encode_query(query)` | 编码单个查询文本 |

**关键实现细节：**

```python
def generate_embeddings(chunks, batch_size=16):
    model = _get_model()  # 全局单例，只加载一次
    embeddings = []
    for i in range(0, total, batch_size):
        vectors = model.encode(texts, convert_to_numpy=True)
        # 每个 chunk 记录：content + source + filename + chunk_id + embedding
        for chunk, vector in zip(batch, vectors):
            embeddings.append({
                **chunk,  # 保留原始元数据
                "embedding": vector.tolist(),  # numpy → list 便于 JSON 序列化
            })
    return embeddings
```

**全局模型缓存**：模型以单例模式加载，避免重复加载大量内存，首次加载后常驻内存。

---

### 5.5 FAISS 索引构建 (rag_05_faiss_goujian.py)

> **文件**: [backend/rag_05_faiss_goujian.py](backend/rag_05_faiss_goujian.py)

基于 Facebook FAISS 库构建余弦相似度向量索引：

**技术要点：**

- 使用 `IndexFlatIP`（内积索引）
- 向量先做 **L2 归一化**，内积等价于余弦相似度
- 索引保存前 `cd` 到目标目录，避免中文路径导致 FAISS C++ 底层访问失败

**核心函数：**

| 函数 | 作用 |
|------|------|
| `build_faiss_index(kb_name, embeddings)` | 构建并保存索引 + 元数据 |
| `load_faiss_index(kb_name)` | 加载已有索引（运行时使用） |
| `index_exists(kb_name)` | 检查索引是否已构建 |
| `build_all_indexes()` | 批量构建所有知识库索引 |

**元数据结构：**

```json
[
  {
    "content": "东巴文化是纳西族的传统...",
    "source": "knowledge_bases/dongba/东巴文化.txt",
    "filename": "东巴文化.txt",
    "chunk_id": 0,
    "embedding": [0.0123, -0.0456, ...],  // 384 维向量
    "create_time": "2026-06-09 12:00:00"
  }
]
```

元数据中保留了完整的 embedding 向量，供 MMR 重排序时计算候选向量间的相似度。

---

### 5.6 MMR 检索 (rag_06_jiansuo_mmr.py)

> **文件**: [backend/rag_06_jiansuo_mmr.py](backend/rag_06_jiansuo_mmr.py)

这是检索的核心模块，实现 **MMR（Maximal Marginal Relevance）** 重排序算法：

**MMR 原理：**

```
MMR = λ × Sim(query, doc) - (1-λ) × max(Sim(doc, already_selected))
```

- **λ = 0.7**：偏向相关性（高分 = 更相关）
- **多样性惩罚**：候选文档与已选中文档的最大相似度
- **平衡效果**：结果既相关又覆盖不同方面，避免多条相似内容

**完整检索流程：**

```
用户问题
  ↓
1. 编码为 384维向量
2. L2 归一化
  ↓
3. FAISS 粗排召回 Top-20（余弦相似度）
4. 过滤 score < 0.01 的结果
  ↓
5. MMR 重排序：
   - 从 20 中选出与查询最相关的一个
   - 循环选择“相关性高 + 与已选够不一样”的结果
   - 直到 5 个
  ↓
6. 返回 [{content, source, filename, score}]
```

**智能拒绝机制：**

- 若所有候选分数低于 `score_threshold`（0.01），返回系统提示
- 在 API 层（rag_01_app.py）额外检查：最高分低于 0.40 时拒绝回答
- 这有效防止跨知识库的噪声匹配

**全局缓存：**

```python
_index_cache: dict[str, faiss.IndexFlatIP] = {}      # 索引缓存
_metadata_cache: dict[str, list[dict]] = {}           # 元数据缓存
_query_encoder = None                                 # 查询编码器单例
```

运行时首次查询某知识库时加载其索引和元数据到内存，后续查询直接使用缓存。知识库更新后调用 `clear_kb_cache(kb_name)` 清除缓存。

**核心函数：**

| 函数 | 作用 |
|------|------|
| `mmr_search(query, kb_name)` | 完整 MMR 检索流程 |
| `clear_kb_cache(kb_name)` | 清除指定/全部缓存（更新后调用） |

---

### 5.7 对话历史 (rag_07_duihua_jilu.py)

> **文件**: [backend/rag_07_duihua_jilu.py](backend/rag_07_duihua_jilu.py)

以 JSON 文件持久化存储对话历史：

**设计要点：**

- 每个会话一个 JSON 文件：`conversation_history/{session_id}.json`
- 自动裁剪：保留最近 `MAX_HISTORY_ROUNDS`（20）轮对话
- 全局会话管理器管理多个会话生命周期

**ChatHistory 类：**

```python
class ChatHistory:
    def __init__(self, session_id: str = "default"): ...
    def add(self, question: str, answer_data: dict): ...   # 添加一轮对话
    def get_history_text(self, max_rounds=10) -> str:       # 格式化历史文本
        # 返回: "用户: xxx\n助手: xxx\n..."
    def get_all(self) -> list[dict]: ...
    def delete_message(self, msg_id: int) -> bool: ...
    def clear(self): ...
    def export(self) -> str: ...                            # 导出为可读文本
```

**会话管理器：**

```python
class SessionManager:
    _sessions: dict[str, ChatHistory]  # 内存缓存

    def get_session(self, session_id) -> ChatHistory: ...
    def list_sessions(self) -> list[dict]: ...   # 扫描所有 JSON 文件
    def delete_session(self, session_id): ...
    def clear_all(self): ...

session_manager = SessionManager()  # 全局单例
```

**JSON 存储格式：**

```json
{
  "session_id": "default",
  "updated_at": "2026-06-09T12:00:00",
  "messages": [
    {
      "id": 1,
      "timestamp": "2026-06-09T12:00:00",
      "question": "东巴文化有什么特点？",
      "answer": "东巴文化是纳西族的...",
      "score": 0.92,
      "sources": [{"filename": "东巴文化.txt", "score": 0.92}]
    }
  ]
}
```

---

### 5.8 FastAPI 主程序 (rag_01_app.py)

> **文件**: [backend/rag_01_app.py](backend/rag_01_app.py)

REST API 服务入口，集成所有模块：

**API 路由一览：**

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/kb/list` | 知识库列表 |
| GET | `/api/kb/{name}/info` | 知识库详情 |
| POST | `/api/kb/build` | 构建单个知识库索引 |
| POST | `/api/kb/build-all` | 一键构建全部知识库 |
| POST | `/api/kb/create` | 创建新知识库（空目录） |
| DELETE | `/api/kb/{name}` | 删除知识库（含所有文件） |
| POST | `/api/kb/{name}/upload` | 上传文档（支持多文件） |
| DELETE | `/api/kb/{name}/documents/{filename}` | 删除指定文档 |
| POST | `/api/chat` | **核心问答接口** |
| GET | `/api/history` | 获取对话历史 |
| GET | `/api/history/sessions` | 列出所有会话 |
| DELETE | `/api/history` | 清空历史 |
| DELETE | `/api/history/sessions/{id}` | 删除会话 |
| POST | `/api/feedback` | 用户反馈 |

**核心问答接口 (/api/chat) 完整逻辑：**

```python
@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    # 1. 验证知识库存在
    # 2. 检查 FAISS 索引已构建
    # 3. MMR 检索：mmr_search(question, kb_name)
    # 4. 命中判断：最高分 < 0.40 则拒绝回答
    # 5. 获取历史对话上下文
    # 6. 构建 Prompt（参考 + 历史 + 规则）
    # 7. 调用千问 API
    # 8. 保存对话历史
    # 9. 返回答案 + 来源列表
```

**知识库显示名称映射：**

```python
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
```

**响应模型：**

```python
class ChatResponse(BaseModel):
    answer: str                          # AI 回答
    sources: list[SourceItem]            # 参考来源列表
    session_id: str                      # 会话 ID

class SourceItem(BaseModel):
    filename: str                        # 源文件名
    source: str                          # 完整路径
    content: str                         # 内容片段（前 300 字）
    score: float                         # 相似度分数
```

**自动重建机制：**

上传文档或删除文档时，`auto_rebuild` 参数（默认 True）可自动触发完整重建流程：
`加载文档 → 切分 → Embedding → FAISS 索引 → 清除缓存`

---

### 5.9 知识库构建脚本 (build_kb.py)

> **文件**: [backend/build_kb.py](backend/build_kb.py)

离线批量构建工具，一次执行为所有知识库生成 Chunk → Embedding → FAISS 索引：

```python
def main():
    for kb_name in list_knowledge_bases():
        chunks = build_chunks(kb_name)        # 切分
        embeddings = generate_embeddings(chunks)  # 编码
        save_embeddings(embeddings, kb_name)
        build_faiss_index(kb_name, embeddings)    # 建索引
```

---

## 6. 前端架构

### 6.1 API 层 (api/index.ts)

> **文件**: [frontend/src/api/index.ts](frontend/src/api/index.ts)

封装所有后端 API 调用，使用原生 `fetch`：

```typescript
export async function chat(question: string, kb: string, sessionId: string) {
  const res = await fetch(`${BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, knowledge_base: kb, session_id: sessionId }),
  })
  if (!res.ok) throw new Error((await res.json()).detail)
  return res.json()
}
```

**所有 API 函数：**

| 函数 | 对应接口 |
|------|----------|
| `listKB()` | GET `/api/kb/list` |
| `getKBInfo(name)` | GET `/api/kb/{name}/info` |
| `buildKB(name)` | POST `/api/kb/build?kb_name=...` |
| `createKB(name)` | POST `/api/kb/create` |
| `deleteKB(name)` | DELETE `/api/kb/{name}` |
| `uploadDocuments(name, files)` | POST `/api/kb/{name}/upload` |
| `deleteDocument(kb, filename)` | DELETE `/api/kb/{name}/documents/{filename}` |
| `chat(question, kb, sessionId)` | POST `/api/chat` |
| `getHistory(sessionId)` | GET `/api/history` |
| `listSessions()` | GET `/api/history/sessions` |
| `deleteSession(sessionId)` | DELETE `/api/history/sessions/{id}` |
| `clearHistory(sessionId)` | DELETE `/api/history` |
| `submitFeedback(msgId, type)` | POST `/api/feedback` |

---

### 6.2 状态管理 (hooks/useChat.ts)

> **文件**: [frontend/src/hooks/useChat.ts](frontend/src/hooks/useChat.ts)

使用 React hooks 管理所有应用状态：

**管理状态：**

```typescript
interface ChatState {
  messages: Message[]           // 当前会话消息列表
  kbs: KnowledgeBase[]          // 知识库列表
  currentKB: string             // 当前选中的知识库
  isLoading: boolean            // 是否正在请求
  sessionId: string             // 当前会话 ID
  sessionTick: number           // 用于触发会话列表刷新的计数器
  sidebarOpen: boolean          // 侧边栏是否展开
  showWelcome: boolean          // 是否显示欢迎页
}
```

**核心逻辑：**

- `sendMessage(text)`：发送问题 → `onStart` 清空欢迎页 → `onFinally` 设置 loading → 调用 API → 追加回复到消息列表
- `switchKB(name)`：切换知识库（保留当前会话）
- `newSession()`：创建新会话（生成新 UUID）
- `loadSession(sid)`：加载历史会话（调用 `getHistory`）
- `setFeedback(msgId, type)`：记录用户反馈

---

### 6.3 类型定义 (types/index.ts)

> **文件**: [frontend/src/types/index.ts](frontend/src/types/index.ts)

```typescript
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  feedback?: 'like' | 'dislike'
}

export interface Source {
  filename: string
  content: string
  score: number
}

export interface KnowledgeBase {
  name: string
  display_name: string
  indexed: boolean
}

export interface KBDocument {
  filename: string
  size: number
}

export interface HistorySession {
  session_id: string
  updated_at: string
  message_count: number
}
```

---

### 6.4 组件体系

```
App.tsx (主布局)
├── Sidebar.tsx        # 左侧面板
│   ├── KBItem (内嵌)      # 单个知识库（可展开文档列表）
│   ├── 上传弹窗 (内嵌)      # 拖拽/选择文件上传
│   └── 会话列表            # 历史会话切换
├── WelcomePage.tsx     # 首页（首次打开时展示）
│   ├── KBCapsule.tsx     # 知识库推荐标签
│   └── ChatInput.tsx      # 搜索框（首页样式）
├── ChatView.tsx        # 聊天主视图
│   ├── Header.tsx         # 顶部栏（知识库名 + 切换）
│   ├── ChatBubble.tsx     # 消息气泡
│   │   ├── Markdown 渲染    # react-markdown + react-syntax-highlighter
│   │   └── 来源面板         # 可展开的参考来源列表
│   └── ChatInput.tsx      # 聊天输入框
└── ThemeToggle.tsx     # 深色模式切换（浮动右上角）
```

**设计语言（index.css）：**

- 毛玻璃效果：`backdrop-filter: blur(32px)` + 半透明背景 + 内阴影高光
- Apple Vision Pro 风格：72px 高输入框、36px 圆角、渐变高光
- 深色模式：通过 `.dark` CSS 变量切换
- 动画：Framer Motion 驱动的淡入、滑动、脉冲动画

---

## 7. RAG 检索细节

### 7.1 向量编码细节

**为什么用 bge-small-zh-v1.5？**

- 输出 384 维向量（比 768/1024 维更小，检索更快）
- 专为中文语义匹配优化
- 模型体积小（约 33MB），适合本地 CPU 部署

**编码后 L2 归一化：**

```python
vectors = np.array([e["embedding"] for e in valid], dtype=np.float32)
faiss.normalize_L2(vectors)  # L2 归一化
index = faiss.IndexFlatIP(dim)  # 内积索引
```

L2 归一化后，内积等价于余弦相似度，值域为 [-1, 1]，越接近 1 表示越相似。

### 7.2 MMR 重排序算法

**完整实现：**

```python
def mmr_search(query, kb_name, top_k=5, fetch_k=20, lambda_param=0.7):
    # 1. 编码查询
    query_vec = encoder.encode([query])
    faiss.normalize_L2(query_vec)

    # 2. FAISS 粗排召回 fetch_k 个
    scores, indices = index.search(query_vec, fetch_k)

    # 3. 构建候选集（含向量，供后续计算相似度）
    candidates = []
    for score, idx in zip(scores[0], indices[0]):
        candidates.append({"vector": emb, "score": score})

    # 4. MMR 重排序
    selected = [argmax(relevance)]  # 选最相关的
    while len(selected) < top_k:
        best_mmr = -inf
        for i, candidate in enumerate(candidates):
            if i in selected: continue
            rel = relevance[i]                          # 相关性
            max_sim = max(cos_sim(candidate, selected)) # 多样性惩罚
            mmr = lambda_ * rel - (1-lambda_) * max_sim  # MMR 公式
            if mmr > best_mmr: update_best(i)
        selected.append(best_idx)

    return [candidates[i] for i in selected]
```

**MMR 参数调优建议：**

| `MMR_LAMBDA` | 效果 | 适用场景 |
|:---:|---|------|
| 1.0 | 纯相关性排序（= FAISS 原始排序） | 精确匹配 |
| 0.7 | **平衡模式（默认）** | 通用问答 |
| 0.5 | 相关性 + 多样性各半 | 需要多角度覆盖 |
| 0.3 | 强多样性 | 探索性检索 |

### 7.3 Prompt 构建策略

**模板：**

```
你是一位云南非物质文化遗产知识库问答助手。你当前的知识库是【东巴文化】。

## 历史对话
用户: 之前的问题
助手: 之前的回答

## 参考资料
【参考资料 1】
来源文件: 东巴文化传承.txt
内容:
...

## 用户问题
东巴文化有什么特点？

## 回答规则
1. **用户的问题必须与当前知识库主题相关**才回答。如果用户问的内容明显不属于
   当前知识库，请直接回复："抱歉，当前知识库中没有相关信息..."
2. **以参考资料为核心**：回答的主体信息必须来自参考资料
3. **可少量补充**：参考资料中缺少的细节可以用你自身知识补充，但不超过30%
4. 回答要**结构清晰**、**自然流畅**
5. 在回答末尾列出**参考来源**（文件名）
```

**关键设计：**

- **知识库隔离校验**：通过规则 1 防止跨库回答，保证知识准确性
- **来源追溯**：规则 5 强制模型在回答中引用来源文件
- **历史上下文**：可选拼接最近 10 轮对话，维持多轮对话连贯性
- **补充限制**：模型自身知识不超过 30%，防止幻觉

---

## 8. 知识库管理

### 当前知识库一览

| 拼音名 | 中文名 | 文档数 | 主题 |
|--------|--------|:------:|------|
| dongba | 东巴文化 | 5 | 纳西族东巴文字、绘画、经书、祭祀、传承 |
| puercha | 普洱茶制作技艺 | 5 | 普洱茶历史、工艺、特点、传承、现代发展 |
| zharan | 扎染 | 5 | 扎染历史、工艺、特点、传承、价值 |
| huobajie | 火把节 | 5 | 火把节历史、活动、文化内涵、传承 |
| poshuijie | 泼水节 | 5 | 泼水节历史、活动、文化内涵、传承 |
| kongquewu | 孔雀舞 | 5 | 孔雀舞历史、表演艺术、特点、传承 |
| naxiguyue | 纳西古乐 | 5 | 纳西古乐历史、演奏艺术、特点、传承 |
| jianshuizitao | 建水紫陶 | 5 | 紫陶历史、工艺、特点、代表作品、文化价值 |
| wutong | 乌铜走银 | 5 | 乌铜走银历史、工艺、特点、传承、现代应用 |
| heqingyinqi | 鹤庆银器 | 5 | 银器历史、工艺、特点、传承、现代应用 |
| 福州 | 福建福州 | 1 | 福州文化主题 |

### 每个知识库的文件结构

```
dongba/
├── 东巴文字.txt            # ~1.7 KB 原始文档
├── 东巴绘画.txt            # ~2.4 KB
├── 东巴经书.txt            # ~2.4 KB
├── 东巴祭祀.txt            # ~2.2 KB
├── 东巴文化传承.txt        # ~2.3 KB
├── chunks.txt             # ~13.5 KB 切分结果
├── chunk_embeddings.json   # ~300 KB 向量数据
├── faiss_index.index       # ~50 KB FAISS 二进制索引
└── faiss_metadata.json     # ~300 KB 元数据（含完整向量）
```

---

## 9. API 接口列表

### 问答

```
POST /api/chat

Request:
{
  "question": "东巴文化有什么特点？",
  "knowledge_base": "dongba",
  "session_id": "default"
}

Response:
{
  "answer": "东巴文化是纳西族的传统宗教文化...",
  "sources": [
    {
      "filename": "东巴文化传承.txt",
      "source": "knowledge_bases/dongba/东巴文化传承.txt",
      "content": "东巴文化是纳西族传统文化的重要组成部分...",
      "score": 0.9234
    }
  ],
  "session_id": "default"
}
```

### 健康检查

```
GET /api/health
Response: { "status": "ok", "version": "1.0.0", "knowledge_bases": 11, "model": "qwen-turbo" }
```

### 知识库管理

```
# 列出所有知识库
GET /api/kb/list
Response: { "knowledge_bases": [{ "name": "dongba", "display_name": "东巴文化", "indexed": true }], "total": 11 }

# 知识库详情
GET /api/kb/{kb_name}/info
Response: { "name": "dongba", "display_name": "东巴文化", "document_count": 5, "indexed": true, "chunk_count": 42 }

# 构建索引
POST /api/kb/build?kb_name=dongba
Response: { "status": "success", "chunks": 42, "embeddings": 42, "vectors": 42 }

# 一键构建全部
POST /api/kb/build-all
Response: { "status": "completed", "success": 10, "failed": 0, "results": [...] }

# 创建知识库
POST /api/kb/create
Body: { "name": "my_kb" }
Response: { "status": "ok", "name": "my_kb" }

# 上传文档
POST /api/kb/{kb_name}/upload
Body: multipart/form-data (files[], auto_rebuild=true)
Response: { "status": "ok", "uploaded": [...], "uploaded_count": 3 }

# 删除文档
DELETE /api/kb/{kb_name}/documents/{filename}?auto_rebuild=true

# 删除整个知识库
DELETE /api/kb/{kb_name}
```

### 对话历史

```
# 获取历史
GET /api/history?session_id=default
Response: { "session_id": "default", "messages": [...], "total": 5 }

# 列出所有会话
GET /api/history/sessions
Response: { "sessions": [{ "session_id": "...", "updated_at": "...", "message_count": 3 }] }

# 清空历史
DELETE /api/history?session_id=default

# 删除会话
DELETE /api/history/sessions/{session_id}

# 用户反馈
POST /api/feedback
Body: { "message_id": "...", "type": "like" }
```

---

## 10. 环境配置

### .env 文件

```bash
# 阿里千问（Qwen）API Key（必填）
DASHSCOPE_API_KEY=your-qwen-api-key-here

# 千问 API 地址
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 大模型名称（可选: qwen-turbo / qwen-plus / qwen-max）
QWEN_MODEL=qwen-turbo
```

### Python 依赖 (requirements.txt)

```
streamlit
openai
sentence-transformers
faiss-cpu
scikit-learn
numpy
pandas
python-docx
PyPDF2
tqdm
torch
transformers
```

> **注意**：虽然 `streamlit` 在依赖列表中，但实际后端使用的是 FastAPI（非 Streamlit）。

---

## 11. 启动与部署

### 开发环境

#### 1. 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 填入你的 DASHSCOPE_API_KEY
```

#### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

#### 3. 构建知识库（构建向量索引）

```bash
cd backend
python build_kb.py
```

> 这会为所有知识库执行：文档加载 → 切分(Chunk) → Embedding编码 → FAISS索引构建

#### 4. 启动后端

```bash
# 方式一：直接启动
cd backend
python rag_01_app.py
# 启动在 http://localhost:8000
# API 文档: http://localhost:8000/docs

# 方式二：通过 run.py（自动配置 Python 路径）
python run.py
# 启动在 http://localhost:8001
```

#### 5. 安装前端依赖

```bash
cd frontend
npm install
```

#### 6. 启动前端

```bash
cd frontend
npm run dev
# 启动在 http://localhost:5173
```

#### 一键启动（Windows）

```bash
start.bat
# 自动执行：构建知识库 → 启动后端(8000) → 启动前端(5173)
```

### 部署注意事项

1. **Embedding 模型**：`bge-small-zh-v1.5/` 目录需要完整部署，包含 `model.safetensors`（或 `pytorch_model.bin`）及配套配置文件
2. **知识库数据**：`knowledge_bases/` 目录需要部署，但其中的 `.index`/`.json` 索引文件可在部署后通过 `build_kb.py` 重新生成
3. **CORS**：后端配置了 `allow_origins=["*"]`，生产环境应限制为具体前端域名
4. **API Key**：通过 `.env` 文件配置，不要提交到 Git
5. **模型文件较大**：`bge-small-zh-v1.5/model.safetensors`（约 33MB）+ `pytorch_model.bin`（约 33MB），注意磁盘空间

---

## 附：数据统计

| 指标 | 数据 |
|------|------|
| 知识库总数 | 11 个 |
| 每个知识库文档数 | 1～5 个 |
| Chunk 大小 | 500 字符 |
| Chunk 重叠 | 100 字符 |
| 向量维度 | 384 维 |
| FAISS 粗排召回 | Top-20 |
| MMR 最终返回 | Top-5 |
| 相似度阈值（拒绝） | 0.40 |
| 最大历史轮次 | 20 轮 |
| 模型名称 | bge-small-zh-v1.5 |
| 大模型 | qwen-turbo（可配置） |

---

*文档生成日期：2026-06-09*
*项目：云南非物质文化遗产智能问答系统 (RAG)*
