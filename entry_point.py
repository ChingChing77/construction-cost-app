# -*- coding: utf-8 -*-
"""
建筑工程造价成本分析集成软件 - exe 入口文件
启动后端 FastAPI 服务 + Streamlit 前端
"""

import sys
import os
import signal
import threading
import time
import socket

# 获取可执行文件所在目录（PyInstaller 打包后）
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
    # 打包后工作目录设为 exe 所在目录
    os.chdir(BASE_DIR)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)


def get_local_ip():
    """获取本机局域网 IP"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def is_port_in_use(port: int) -> bool:
    """检查端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def init_app():
    """初始化数据库"""
    try:
        from database import init_database, init_sample_data
        init_database()
        init_sample_data()
        print("[✓] 数据库初始化完成")
    except Exception as e:
        print(f"[!] 数据库初始化失败: {e}")


def run_backend():
    """启动 FastAPI 后端（uvicorn）"""
    try:
        import uvicorn
        # 直接导入 app 对象，避免 frozen 环境下找不到 'main' 模块
        if getattr(sys, "frozen", False):
            # 打包后：app 已在 init_app 中导入
            from main import app as fastapi_app
        else:
            from main import app as fastapi_app

        print("[启动] FastAPI 后端 → http://localhost:8000/docs")
        uvicorn.run(
            fastapi_app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="warning",
        )
    except Exception as e:
        print(f"[!] 后端启动失败: {e}")


def run_frontend():
    """启动 Streamlit 前端"""
    try:
        import subprocess
        streamlit_script = os.path.join(BASE_DIR, "streamlit_app.py")
        # 如果打包后 streamlit_app.py 不在 BASE_DIR，尝试当前目录
        if not os.path.exists(streamlit_script):
            streamlit_script = "streamlit_app.py"
        print("[启动] Streamlit 前端 → http://localhost:8501")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            streamlit_script,
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
        ], cwd=BASE_DIR)
    except Exception as e:
        print(f"[!] 前端启动失败: {e}")


def main():
    print("=" * 60)
    print("  建筑工程造价成本分析集成软件")
    print("=" * 60)

    local_ip = get_local_ip()

    print()
    print("  [1] 初始化数据库 ...")
    init_app()
    print()
    print("  [2] 启动 FastAPI 后端服务（端口 8000）...")
    print("  [3] 启动 Streamlit 前端界面（端口 8501）")
    print()
    print(f"  ✅ 访问地址：")
    print(f"     本机: http://localhost:8501")
    print(f"     局域网: http://{local_ip}:8501")
    print()
    print("  按 Ctrl+C 或关闭此窗口即可停止服务")
    print("=" * 60)

    # 注册信号处理（支持 Ctrl+C 和窗口关闭）
    shutdown_event = threading.Event()

    def signal_handler(signum, frame):
        print("\n[停止] 正在关闭服务 ...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 后端线程
    backend_thread = threading.Thread(target=run_backend, daemon=False)
    backend_thread.start()

    # 等待后端启动
    time.sleep(2)

    # 前端线程
    frontend_thread = threading.Thread(target=run_frontend, daemon=False)
    frontend_thread.start()

    # 主线程等待信号
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
            if not backend_thread.is_alive() and not shutdown_event.is_set():
                print("[!] 后端意外退出，正在重启 ...")
                backend_thread = threading.Thread(target=run_backend, daemon=False)
                backend_thread.start()
    except KeyboardInterrupt:
        pass
    finally:
        print("[退出] 服务已停止")


if __name__ == "__main__":
    main()
