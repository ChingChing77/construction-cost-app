# -*- coding: utf-8 -*-
"""
PyInstaller spec 文件 - 建筑工程造价成本分析集成软件
仅打包启动器，真正的服务由子进程启动
"""

import os
import sys

block_cipher = None
PROJECT_DIR = os.path.dirname(os.path.abspath(SPEC))

a = Analysis(
    ["launcher.py"],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=[
        (os.path.join(PROJECT_DIR, "main.py"), "."),
        (os.path.join(PROJECT_DIR, "streamlit_app.py"), "."),
        (os.path.join(PROJECT_DIR, "database.py"), "."),
        (os.path.join(PROJECT_DIR, "config.py"), "."),
        (os.path.join(PROJECT_DIR, "requirements.txt"), "."),
    ],
    hiddenimports=[
        "database",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib", "tkinter", "PyQt5", "PyQt6", "PyGObject",
        "test", "pytest", "unittest", "distutils", "setuptools",
        "PySimpleGUI", "pysimplegui",
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
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="建筑工程造价成本分析集成软件",
)
