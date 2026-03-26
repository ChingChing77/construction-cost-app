# -*- coding: utf-8 -*-
"""
PyInstaller spec 文件 - 建筑工程造价成本分析集成软件
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# 项目根目录
PROJECT_DIR = os.path.dirname(os.path.abspath(SPEC))

# 需要收集的隐藏导入
hiddenimports = [
    # FastAPI 生态
    "fastapi",
    "uvicorn",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "starlette",
    "pydantic",
    "pydantic.fields",
    "pydantic.main",
    # Streamlit（核心部分）
    "streamlit",
    "streamlit.runtime",
    "streamlit.runtime.scriptrunner",
    "streamlit.web",
    "streamlit.web.bootstrap",
    "streamlit.elements",
    # 数据处理
    "pandas",
    "pandas.core",
    "openpyxl",
    "plotly",
    "plotly.graph_objects",
    # 业务模块
    "database",
    "analytics",
    "reports",
    "config",
    "data_generator",
    "models",
]

# 收集所有数据文件
datas = [
    # 项目根目录的 .py 文件
    (os.path.join(PROJECT_DIR, "main.py"), "."),
    (os.path.join(PROJECT_DIR, "streamlit_app.py"), "."),
    (os.path.join(PROJECT_DIR, "config.py"), "."),
    (os.path.join(PROJECT_DIR, "database.py"), "."),
    (os.path.join(PROJECT_DIR, "data_generator.py"), "."),
    (os.path.join(PROJECT_DIR, "analytics.py"), "."),
    (os.path.join(PROJECT_DIR, "reports.py"), "."),
    (os.path.join(PROJECT_DIR, "models.py"), "."),
    # requirements.txt
    (os.path.join(PROJECT_DIR, "requirements.txt"), "."),
]

# 收集 reports/ 子目录
reports_dir = os.path.join(PROJECT_DIR, "reports")
if os.path.exists(reports_dir):
    datas.append((reports_dir, "reports"))

# 添加 data/ 目录（如果存在）
data_dir = os.path.join(PROJECT_DIR, "data")
if os.path.exists(data_dir):
    datas.append((data_dir, "data"))

a = Analysis(
    ["entry_point.py"],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "tkinter", "PyQt5", "PyQt6", "PyGObject",
        "test", "pytest", "unittest", "distutils", "setuptools",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    disable_windowed_traceback=True,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="建筑工程造价成本分析集成软件",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="建筑工程造价成本分析集成软件",
)
