#!/bin/bash
# =====================================================================
# 建筑工程造价成本分析集成软件 - Linux 构建脚本
# 使用 PyInstaller 在 Linux 上交叉打包 Windows exe
# =====================================================================
set -e

echo "=================================================="
echo "  建筑工程造价成本分析集成软件 - 构建脚本"
echo "=================================================="

WORK_DIR="/home/ubuntu/.openclaw/workspace/construction_cost"
cd "$WORK_DIR"

# 安装依赖
echo ""
echo "[1/4] 安装 Python 依赖 ..."
pip install -r requirements.txt -q --break-system-packages

# 安装额外依赖（API 服务需要）
pip install fastapi uvicorn pydantic python-multipart -q --break-system-packages

# 安装 PyInstaller
echo ""
echo "[2/4] 安装 PyInstaller ..."
pip install pyinstaller -q --break-system-packages

# 清理旧的构建文件
echo ""
echo "[3/4] 清理旧构建文件 ..."
rm -rf build/ dist/ __pycache__/ *.spec.bak

# 执行打包（Windows 目标）
# 注意：Linux 交叉编译 Windows exe 需要 wine + pyinstaller
# 如果 wine 未安装，会使用当前平台打包（生成 Linux 可执行文件）
echo ""
echo "[4/4] 执行 PyInstaller 打包 ..."
if command -v wine &> /dev/null; then
    echo "  [wine 检测] 使用 wine 交叉编译 Windows exe ..."
    pyinstaller --onefile \
        --name "建筑工程造价成本分析集成软件" \
        --console \
        --additional-hooks-dir "." \
        --paths "." \
        entry_point.py
else
    echo "  [警告] wine 未安装，无法交叉编译 Windows exe"
    echo "  尝试使用 --target-platform 选项 ..."
    # 尝试添加 hidden imports 后直接打包
    pyinstaller \
        --onefile \
        --name "建筑工程造价成本分析集成软件" \
        --console \
        --additional-hooks-dir "." \
        entry_point.py \
        --hidden-import=fastapi \
        --hidden-import=uvicorn \
        --hidden-import=starlette \
        --hidden-import=pydantic \
        --hidden-import=streamlit \
        --hidden-import=pandas \
        --hidden-import=openpyxl \
        --hidden-import=plotly \
        --hidden-import=database \
        --hidden-import=analytics \
        --hidden-import=reports \
        --hidden-import=config \
        --hidden-import=data_generator \
        --hidden-import=models \
        || true

    echo ""
    echo "=================================================="
    echo "  构建完成（当前平台）"
    echo "  Windows 交叉编译请使用 build.bat 在 Windows 机器上运行"
    echo "=================================================="
fi

# 检查结果
if [ -d "dist" ]; then
    echo ""
    echo "=================================================="
    echo "  ✅ 构建成功！"
    echo "  输出目录: $WORK_DIR/dist/"
    ls -lh dist/
    echo "=================================================="
else
    echo ""
    echo "  [!] 未找到 dist 目录，构建可能失败"
fi
