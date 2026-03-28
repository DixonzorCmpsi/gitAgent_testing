@echo off
title Agent Forge (OpenClaw + gitagent)
echo.
echo  ============================================
echo    Agent Forge — OpenClaw + gitagent Fork
echo    Git-auditable, boundary-enforced agents
echo  ============================================
echo.
echo  [1] TUI Chat (lightweight, direct OpenRouter)
echo  [2] OpenClaw Agent (full harness, all tools)
echo  [3] OpenClaw Gateway (web UI at localhost:18789)
echo.
set /p choice="  Select mode [1/2/3]: "

cd /d "%~dp0"

if "%choice%"=="1" (
    python forge-chat.py
) else if "%choice%"=="2" (
    cd openclaw
    node dist/index.js agent --agent main
) else if "%choice%"=="3" (
    cd openclaw
    echo Starting gateway at http://127.0.0.1:18789 ...
    node dist/index.js gateway
) else (
    echo Invalid choice.
)
pause
