# 启动说明（快速上手）

此文档记录如何在本地启动并调试前端与后端（开发模式），以及常见问题的快速排查方法。

项目根目录（工作目录）:

```
D:\yunanfeiyiwenda\pythonProject
```

重要文件：

- 后端启动脚本: backend/rag_01_app.py
- 前端 vite 配置: frontend/vite.config.ts

默认端口（当前仓库配置）

- 后端 (FastAPI / Uvicorn): 8001
- 前端 (Vite dev server): 5174

一、准备环境

1. Python 环境（Windows PowerShell 示例）

   - 建议使用虚拟环境（venv）并激活：

     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     pip install -r backend\requirements.txt
     ```

   - 如果项目没有 requirements.txt，请根据需要安装依赖（FastAPI、uvicorn、pydantic 等）。

2. Node / npm（前端）

   ```powershell
   cd frontend
   npm install
   ```

二、启动后端（开发）

推荐在激活的 Python 虚拟环境中运行：

```powershell
# 从项目根
python backend\rag_01_app.py
# 或直接用 uvicorn（便于指定端口）
uvicorn backend.rag_01_app:app --host 0.0.0.0 --port 8001 --reload
```

启动成功时你会看到类似：

```
INFO: Uvicorn running on http://0.0.0.0:8001
INFO: Application startup complete.
```

并可在浏览器/终端测试健康接口：

```
http://localhost:8001/api/health
```

三、启动前端（开发）

在另一个终端（PowerShell / cmd / Git Bash）中：

```powershell
cd frontend
npm run dev
```

打开页面：

```
http://localhost:5174
```

注意：前端通过相对路径 `/api` 访问后端，Vite dev server 使用 proxy 将 `/api` 转发到 backend。当前配置位于：

frontend/vite.config.ts

若你改动了后端端口，请同时修改该文件中的 `proxy.target` 并重启前端。

四、常见问题与排查

- 前端页面能打开但无法对话 / 切换知识库：通常是前端到后端的 /api 请求失败。
  - 打开浏览器开发者工具 → Network，观察对 `/api/*` 的请求是否返回 200。
  - 确认 vite proxy 指向的端口和后端实际监听端口一致。

- 后端启动时报错 `WinError 10013` 或端口绑定失败：
  - 表示该端口已被其它进程占用或被系统策略阻止。
  - 查看占用情况（PowerShell）：

    ```powershell
    netstat -ano | Select-String ":8000"  # 或 :8001
    Get-Process -Id <PID>
    ```

  - 如果不想停止占用进程，建议改用另一个端口（例如 8001），并同步前端 proxy。

- 在浏览器看到 "使用 HTTPS" / SSL 错误：
  - 说明你访问的端口被某个 HTTPS 服务占用（例如 Apache）。要么使用 https:// 访问，要么换端口给本项目后端。

- 模型/Embedding 加载错误（涉及 CUDA）：
  - 后端某些模块可能会尝试用 GPU（device='cuda'）加载模型，如果系统没有正确安装 CUDA 驱动或没有兼容的 PyTorch，模型加载会失败并导致 API 返回 500。
  - 排查方法：查看后端终端的完整 Traceback，检查文件 `backend/rag_04_xiangliang_bianma.py` 和 `backend/config.py` 中关于 device 的配置；若无 GPU，可临时改成 `device='cpu'`。

五、常用 API（用于验证）

- 健康检查： `GET /api/health`
- 知识库列表： `GET /api/kb/list`
- 构建指定知识库： `POST /api/kb/build?kb_name=<name>`
- 聊天接口： `POST /api/chat` （body 需包含 question、knowledge_base）

六、如果需要我帮你启动服务

- 我可以在当前工作区代为启动后端/前端并把日志贴给你，但这需要你在对话中明确允许我运行 shell 命令。

七、变更记录（我已做的修改）

- 将后端默认端口从 `8000` 改为 `8001`：文件 `backend/rag_01_app.py`
- 将前端 vite proxy 指向 `http://localhost:8001`：文件 `frontend/vite.config.ts`

---
简短提示：启动顺序通常是先后端（确保 /api 可达），再前端（因前端 dev server 会代理 /api）。

