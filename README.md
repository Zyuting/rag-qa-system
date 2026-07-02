# 🏔️ Yuti RAG — 云南非物质文化遗产智能问答系统

> 生产级 **RAG (Retrieval-Augmented Generation)** 知识库问答基础设施  
> 覆盖从文档索引到智能问答的完整链路，支持多知识库、MMR 混合检索与来源追溯

---

## ✨ 功能特性

- 📚 **10 个知识库**：东巴文化、普洱茶、扎染、火把节、泼水节、孔雀舞、纳西古乐、建水紫陶、乌铜走银、鹤庆银器
- 🔒 **知识库隔离**：每个知识库独立向量索引，隔离存储
- 🔍 **FAISS 向量检索**：余弦相似度粗排，高效召回
- 🎯 **MMR 重排序**：平衡检索结果的相关性与多样性，避免内容重复
- 💬 **多会话管理**：对话历史持久化，支持回溯与导出
- 📎 **来源追溯**：每个回答可追溯到原始文档片段与相关性评分
- 🎨 **现代 UI**：Vision Pro 毛玻璃风格 + TailwindCSS + Framer Motion

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
rag-qa-system/
├── .env                        # API Key 配置（不提交 Git）
├── .env.example                # 配置示例
├── pyproject.toml              # 项目元数据与依赖管理
├── requirements.txt            # Python 依赖（pip 兼容）
├── LICENSE                     # MIT 许可证
├── README.md                   # 项目文档
├── start.bat                   # Windows 一键启动脚本
├── start_server.py             # 后端启动入口
│
├── backend/                    # 后端模块
│   ├── __init__.py
│   ├── config.py               # 全局配置
│   ├── rag_01_app.py           # FastAPI 主入口
│   ├── rag_02_zhishiku_jiazai.py  # 文档加载
│   ├── rag_03_wendang_qiefen.py   # 文本切分
│   ├── rag_04_xiangliang_bianma.py # Embedding 编码
│   ├── rag_05_faiss_goujian.py    # FAISS 索引构建
│   ├── rag_06_jiansuo_mmr.py      # MMR 重排序检索
│   ├── rag_07_duihua_jilu.py      # 对话历史管理
│   └── build_kb.py               # 知识库构建脚本
│
├── frontend/                   # React 前端
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
│       ├── App.tsx             # 主布局
│       ├── api/index.ts        # API 封装
│       ├── hooks/useChat.ts    # 状态管理
│       ├── types/index.ts      # TypeScript 类型
│       └── components/
│           ├── Sidebar.tsx     # 知识库管理侧栏
│           ├── ChatView.tsx    # 聊天视图
│           ├── ChatBubble.tsx  # 消息气泡
│           ├── ChatInput.tsx   # 输入框
│           ├── KBCapsule.tsx   # 知识库选择器
│           ├── WelcomePage.tsx # 欢迎页
│           └── ThemeToggle.tsx # 明暗切换
│
├── knowledge_bases/            # 10 个非遗知识库（含样本文档）
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
└── bge-small-zh-v1.5/         # 本地 Embedding 模型（需自行下载）
```

---

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- pip + npm
- [bge-small-zh-v1.5](https://huggingface.co/BAAI/bge-small-zh-v1.5) 模型（自动下载或本地放入项目根目录）

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

后端启动在 http://localhost:8001，API 文档 http://localhost:8001/docs

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

前端启动在 http://localhost:5174

### 一键启动 (Windows)

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
| POST | `/api/kb/build` | 构建知识库索引 |
| POST | `/api/kb/build-all` | 一键构建全部索引 |
| POST | `/api/kb/create` | 创建新知识库 |
| DELETE | `/api/kb/{name}` | 删除知识库 |
| POST | `/api/kb/{name}/upload` | 上传文档 |
| DELETE | `/api/kb/{name}/documents/{filename}` | 删除文档 |
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
