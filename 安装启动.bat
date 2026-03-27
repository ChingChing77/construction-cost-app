@echo off
chcp 65001 >nul
title 建筑工程造价成本分析集成软件
echo ========================================
echo  建筑工程造价成本分析集成软件
echo  自动安装启动工具
echo ========================================
echo.

REM ===== 检查 Python =====
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo.
    echo 请先下载安装 Python 3.11 或更高版本：
    echo   https://www.python.org/downloads/
    echo.
    echo 安装时请务必勾选：Add Python to PATH
    echo.
    pause
    exit /b 1
)

echo [OK] Python 已安装
python --version
echo.

REM ===== 获取脚本目录 =====
set SCRIPT_DIR=%~dp0
cd /d "%SCRIPT_DIR%"

REM ===== 安装依赖 =====
echo [1/3] 检查依赖（首次可能需要几分钟）...
pip install -q streamlit requests plotly pandas openpyxl fastapi uvicorn 2>nul
if errorlevel 1 (
    echo [警告] 部分依赖安装失败，尝试继续...
)
echo.

REM ===== 初始化数据库 =====
echo [2/3] 初始化数据库...
python -c "import sys; sys.path.insert(0,'.'); from database import init_database, init_sample_data; init_database(); init_sample_data(); print('[OK] 数据库就绪')" 2>nul
if errorlevel 1 (
    echo [跳过] 数据库初始化（无数据库模块）
)
echo.

REM ===== 启动服务 =====
echo [3/3] 启动服务...
echo.
echo 正在启动后端（端口 8000）和前端（端口 8501）...
echo 请耐心等待，稍后浏览器将自动打开
echo.
echo 如浏览器未自动打开，请手动访问：
echo   http://localhost:8501
echo.
echo 按 Ctrl+C 可停止服务
echo ========================================
echo.

start "后端服务" cmd /c "python -m uvicorn main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
python -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

pause
