# -*- coding: utf-8 -*-
"""
建筑工程造价成本分析集成软件 - ONEFILE 打包配置
"""

import os, sys

block_cipher = None
PROJECT_DIR = os.path.dirname(os.path.abspath(SPEC))

# 需要收集数据文件的目录
def get_data_files():
    datas = []
    for pyfile in ['main.py', 'streamlit_app.py', 'database.py', 'data_generator.py',
                   'analytics.py', 'reports.py', 'config.py', 'models.py', 'requirements.txt']:
        src = os.path.join(PROJECT_DIR, pyfile)
        if os.path.exists(src):
            datas.append((src, '.'))
    # reports/ 目录
    reports_dir = os.path.join(PROJECT_DIR, 'reports')
    if os.path.exists(reports_dir):
        datas.append((reports_dir, 'reports'))
    return datas

a = Analysis(
    ['launcher.py'],
    pathex=[PROJECT_DIR],
    binaries=[],
    datas=get_data_files(),
    hiddenimports=[
        # FastAPI生态
        'fastapi',
        'uvicorn',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'starlette',
        'starlette.requests',
        'starlette.responses',
        'pydantic',
        'pydantic.fields',
        'pydantic.main',
        # Streamlit
        'streamlit',
        'streamlit.runtime',
        'streamlit.runtime.scriptrunner',
        'streamlit.web',
        'streamlit.web.bootstrap',
        'streamlit.elements',
        # 数据处理
        'pandas',
        'pandas.core',
        'openpyxl',
        'plotly',
        'plotly.graph_objects',
        # 业务模块
        'database',
        'analytics',
        'reports',
        'config',
        'data_generator',
        'models',
        # 报告
        'jinja2',
        'openpyxl',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'tkinter', 'PyQt5', 'PyQt6', 'PyGObject',
        'test', 'pytest', 'unittest', 'distutils', 'setuptools',
        'PySimpleGUI', 'pysimplegui',
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
    name='建筑工程造价成本分析集成软件',
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
