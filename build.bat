@echo off
chcp 65001 >nul
:: =====================================================================
:: 建筑工程造价成本分析集成软件 - Windows 构建脚本
:: 在 Windows 机器上双击运行，或在 cmd/PS 中执行
:: =====================================================================

echo ==================================================
echo   建筑工程造价成本分析集成软件 - Windows 构建
echo ==================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.9+
    echo   下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 安装依赖
echo [1/4] 安装 Python 依赖 ...
pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

:: 安装 API 服务依赖
echo.
echo [2/4] 安装 FastAPI 服务依赖 ...
pip install fastapi uvicorn pydantic python-multipart
if errorlevel 1 (
    echo [错误] API 依赖安装失败
    pause
    exit /b 1
)

:: 安装 PyInstaller
echo.
echo [3/4] 安装 PyInstaller ...
pip install pyinstaller
if errorlevel 1 (
    echo [错误] PyInstaller 安装失败
    pause
    exit /b 1
)

:: 清理旧构建
echo.
echo [4/4] 清理旧构建文件 ...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

:: 执行打包
echo.
echo ==================================================
echo   开始打包（onefile 模式）
echo ==================================================
pyinstaller --onefile --name "建筑工程造价成本分析集成软件" --console main.spec

:: 检查结果
if exist "dist\建筑工程造价成本分析集成软件.exe" (
    echo.
    echo ==================================================
    echo   打包成功！
    echo   输出文件: dist\建筑工程造价成本分析集成软件.exe
    echo ==================================================
) else (
    echo.
    echo [警告] 未找到 exe 文件，可能打包有问题
)

pause
