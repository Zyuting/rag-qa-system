# 🏔️ 云南非物质文化遗产智能问答系统

> 基于 **RAG**（Retrieval-Augmented Generation）技术的云南非遗知识库智能助手

---

## ✨ 功能特性

- 📚 **10 个知识库**：东巴文化、普洱茶、扎染、火把节、泼水节、孔雀舞、纳西古乐、建水紫陶、乌铜走银、鹤庆银器
- 🔒 **知识库隔离**：每个知识库独立存储和管理
- 🔍 **向量检索**：FAISS 高效余弦相似度检索
- 🎯 **MMR 重排序**：平衡检索结果的相关性与多样性
- 💬 **对话历史**：多会话管理，支持历史查看和导出
- 📎 **来源追溯**：每个回答可追溯到原始文档片段
- 🎨 **现代 UI**：Apple Glass + ChatGPT 极简风格，毛玻璃卡片 + 渐变高光

---

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python 3.11 + FastAPI + Uvicorn |
| 向量检索 | FAISS (CPU) |
| Embedding | bge-small-zh-v1.5 (BAAI) |
| 大模型 | 阿里千问 (Qwen API, OpenAI 兼容) |
| 前端框架 | React 18 + Vite + TypeScript |
| 样式 | TailwindCSS + Framer Motion |
| 文档解析 | PyPDF2 + python-docx |

---

## 📁 项目结构

```
pythonProject/
├── .env                        # API Key 配置（不提交 Git）
├── .env.example                # 配置示例
├── requirements.txt            # Python 依赖
├── README.md                   # 项目文档
├── start.bat                   # 一键启动脚本
│
├── backend/                    # 后端模块
│   ├── config.py               # 全局配置
│   ├── rag_01_app.py           # FastAPI 主入口
│   ├── rag_02_zhishiku_jiazai.py  # 文档加载
│   ├── rag_03_wendang_qiefen.py   # 文本切分
│   ├── rag_04_xiangliang_bianma.py # Embedding 编码
│   ├── rag_05_faiss_goujian.py    # FAISS 索引构建
│   ├── rag_06_jiansuo_mmr.py      # MMR 检索
│   ├── rag_07_duihua_jilu.py      # 对话历史
│   └── build_kb.py            # 知识库构建脚本
│
├── frontend/                   # 前端项目
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx             # 主布局（三栏）
│       ├── api/index.ts        # API 调用
│       ├── hooks/useChat.ts    # 状态管理
│       ├── types/index.ts      # TypeScript 类型
│       └── components/
│           ├── Header.tsx      # 顶部导航
│           ├── Sidebar.tsx     # 左侧知识库栏
│           ├── ChatWindow.tsx  # 聊天窗口
│           ├── ChatBubble.tsx  # 聊天气泡
│           ├── ChatInput.tsx   # 输入框
│           └── SourcePanel.tsx # 来源追溯面板
│
├── knowledge_bases/            # 10 个知识库（已有）
│   ├── dongba/                 # 东巴文化
│   ├── puercha/                # 普洱茶制作技艺
│   ├── zharan/                 # 扎染
│   ├── huobajie/               # 火把节
│   ├── poshuijie/              # 泼水节
│   ├── kongquewu/              # 孔雀舞
│   ├── naxiguyue/              # 纳西古乐
│   ├── jianshuizitao/          # 建水紫陶
│   ├── wutong/                 # 乌铜走银
│   └── heqingyinqi/            # 鹤庆银器
│
└── bge-small-zh-v1.5/         # Embedding 模型文件（已有）
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- pip + npm

### 1. 配置 API Key

编辑 `.env` 文件：

```bash
DASHSCOPE_API_KEY=your-qwen-api-key-here
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-turbo
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 3. 构建知识库

```bash
cd backend
python build_kb.py
```

这会为所有 10 个知识库生成 Chunk → Embedding → FAISS 索引。

### 4. 启动后端

```bash
cd backend
python rag_01_app.py
```

后端启动在 http://localhost:8000，API 文档 http://localhost:8000/docs

### 5. 安装前端依赖

```bash
cd frontend
npm install
```

### 6. 启动前端

```bash
cd frontend
npm run dev
```

前端启动在 http://localhost:5173

### 一键启动

Windows:
```bash
start.bat
```

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/chat` | 智能问答 |
| GET | `/api/kb/list` | 知识库列表 |
| GET | `/api/kb/{name}/info` | 知识库详情 |
| POST | `/api/kb/build` | 构建单个知识库 |
| POST | `/api/kb/build-all` | 一键构建全部 |
| GET | `/api/history` | 获取对话历史 |
| DELETE | `/api/history` | 清空历史 |
| GET | `/api/health` | 健康检查 |

### 问答请求示例

```json
POST /api/chat
{
  "question": "东巴文化有什么特点？",
  "knowledge_base": "dongba",
  "session_id": "default"
}
```

### 响应示例

```json
{
  "answer": "东巴文化是纳西族的传统宗教文化...",
  "sources": [
    {
      "filename": "东巴文化传承.txt",
      "source": "knowledge_bases/dongba/东巴文化传承.txt",
      "content": "...",
      "score": 0.9234
    }
  ],
  "session_id": "default"
}
```

---

## 🔄 RAG 流程

```
用户提问
  → Embedding 编码（bge-small-zh-v1.5）
  → FAISS 粗排召回 Top-20
  → MMR 重排序 Top-5
  → 构建 Prompt（历史 + 参考上下文 + 问题）
  → Qwen API 生成回答
  → 返回回答 + 来源追溯
```

---

## 📄 License

本项目仅用于学习和毕业设计目的。
