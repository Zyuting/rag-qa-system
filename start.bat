@echo off
chcp 65001 >nul
title 云南非遗智能问答系统

echo.
echo ════════════════════════════════════════════════════════
echo    🏔️  云南非物质文化遗产智能问答系统
echo ════════════════════════════════════════════════════════
echo.

REM ────────── 检查 .env ──────────
if not exist ".env" (
    echo [WARN] .env 文件不存在，正在从 .env.example 创建...
    copy .env.example .env
    echo [INFO] 请编辑 .env 文件填入你的 API Key
)

REM ────────── Step 1: 构建知识库 ──────────
echo.
echo [Step 1/3] 构建知识库索引...
echo.
call .venv\Scripts\activate.bat
cd backend
python build_kb.py
cd ..
echo.

REM ────────── Step 2: 启动后端 ──────────
echo [Step 2/3] 启动后端服务 (端口 8001)...
echo.
start "Backend-API" cmd /k "cd /d %cd% && .venv\Scripts\activate.bat && cd backend && ..\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8001 --reload"

REM 等待后端启动
echo 等待后端启动...
timeout /t 5 /nobreak >nul

REM ────────── Step 3: 启动前端 ──────────
echo.
echo [Step 3/3] 启动前端服务 (端口 5173)...
echo.
start "Frontend-UI" cmd /k "cd /d %cd%\frontend && npm run dev"

echo.
echo ════════════════════════════════════════════════════════
echo   ✅ 启动完成！
echo.
echo   后端 API: http://localhost:8001
echo   API 文档: http://localhost:8001/docs
echo   前端界面: http://localhost:5173
echo ════════════════════════════════════════════════════════
echo.
echo 按任意键退出此窗口（不会关闭后端和前端）...
pause >nul
