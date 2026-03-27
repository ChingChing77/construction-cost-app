@echo off
chcp 65001 >nul
echo ========================================
echo  建筑工程造价成本分析集成软件
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python！
    echo 请先从 https://www.python.org/downloads/ 下载安装 Python 3.11 或更高版本
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)

echo [1/4] 检查依赖安装状态...
pip show streamlit >nul 2>&1
if errorlevel 1 (
    echo [2/4] 安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败！
        pause
        exit /b 1
    )
)

echo [3/4] 启动后端服务 (端口 8000)...
start "FastAPI后端" python -m uvicorn main:app --host 0.0.0.0 --port 8000

echo [4/4] 启动前端界面 (端口 8501)...
python -m streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true

pause
