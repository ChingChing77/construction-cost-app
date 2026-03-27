# -*- coding: utf-8 -*-
"""
建筑工程造价成本分析集成软件 - 独立启动器
启动后端 + 打开浏览器访问网页
"""

import sys
import os
import socket
import webbrowser
import time
import threading
import subprocess

# ====================== 配置 ======================
PORT_BACKEND = 8000
PORT_FRONTEND = 8501
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ====================== 工具函数 ======================

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


def is_port_open(port):
    """检查端口是否开放"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def wait_for_port(port, timeout=30):
    """等待端口就绪"""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_open(port):
            return True
        time.sleep(0.5)
    return False


# ====================== 启动后端 ======================

def init_database():
    """初始化数据库"""
    print("[数据库] 初始化中...")
    try:
        sys.path.insert(0, BASE_DIR)
        from database import init_database, init_sample_data
        init_database()
        init_sample_data()
        print("[数据库] ✅ 初始化完成")
        return True
    except Exception as e:
        print(f"[数据库] ❌ 初始化失败: {e}")
        return False


def run_backend():
    """启动 FastAPI 后端"""
    print("[后端] 启动 FastAPI 服务...")
    try:
        backend_script = os.path.join(BASE_DIR, "backend_server.py")
        if not os.path.exists(backend_script):
            # 直接启动 uvicorn
            proc = subprocess.Popen(
                [sys.executable, "-m", "uvicorn",
                 "main:app", "--host", "0.0.0.0", "--port", str(PORT_BACKEND)],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            proc = subprocess.Popen(
                [sys.executable, backend_script],
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        return proc
    except Exception as e:
        print(f"[后端] ❌ 启动失败: {e}")
        return None


def run_frontend():
    """启动 Streamlit 前端"""
    print("[前端] 启动 Streamlit...")
    try:
        streamlit_script = os.path.join(BASE_DIR, "streamlit_app.py")
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run",
             streamlit_script,
             "--server.port", str(PORT_FRONTEND),
             "--server.address", "0.0.0.0",
             "--server.headless", "true"],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return proc
    except Exception as e:
        print(f"[前端] ❌ 启动失败: {e}")
        return None


# ====================== 主程序 ======================

def main():
    print()
    print("=" * 60)
    print("  建筑工程造价成本分析集成软件 v1.0")
    print("=" * 60)
    print()

    local_ip = get_local_ip()

    # 1. 初始化数据库
    if not init_database():
        print("\n⚠️  数据库初始化失败，但继续启动服务...\n")

    # 2. 启动后端
    print()
    backend_proc = run_backend()
    if backend_proc is None:
        print("❌ 后端启动失败，请检查 Python 环境")
        input("按回车键退出...")
        return

    # 3. 等待后端就绪
    print(f"[后端] 等待服务就绪 (端口 {PORT_BACKEND})...")
    if not wait_for_port(PORT_BACKEND, timeout=20):
        print(f"❌ 后端服务启动超时 (端口 {PORT_BACKEND} 未响应)")
        input("按回车键退出...")
        return
    print(f"[后端] ✅ 已就绪 → http://localhost:{PORT_BACKEND}/docs")

    # 4. 启动前端
    print()
    frontend_proc = run_frontend()
    if frontend_proc is None:
        print("❌ 前端启动失败")
        backend_proc.terminate()
        input("按回车键退出...")
        return

    # 5. 等待前端就绪
    print(f"[前端] 等待界面就绪 (端口 {PORT_FRONTEND})...")
    if not wait_for_port(PORT_FRONTEND, timeout=30):
        print(f"⚠️  前端启动超时，尝试直接访问...")
    else:
        print(f"[前端] ✅ 已就绪 → http://localhost:{PORT_FRONTEND}")

    # 6. 打开浏览器
    print()
    print(f"🌐 正在打开浏览器...")
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT_FRONTEND}")

    print()
    print("=" * 60)
    print(f"  ✅ 系统已就绪！")
    print()
    print(f"  📱 访问地址：")
    print(f"     本机:    http://localhost:{PORT_FRONTEND}")
    print(f"     局域网: http://{local_ip}:{PORT_FRONTEND}")
    print(f"     API文档: http://localhost:{PORT_BACKEND}/docs")
    print()
    print(f"  按 Ctrl+C 停止服务")
    print("=" * 60)

    # 6. 保持运行
    try:
        while True:
            time.sleep(2)
            # 检查进程是否存活
            if backend_proc.poll() is not None:
                print("\n⚠️  后端进程已退出，正在重启...")
                backend_proc = run_backend()
                if backend_proc and wait_for_port(PORT_BACKEND, 10):
                    print("[后端] 重启成功")
            if frontend_proc.poll() is not None:
                print("\n⚠️  前端进程已退出")
                break
    except KeyboardInterrupt:
        print("\n\n[停止] 正在关闭服务...")
    finally:
        if backend_proc:
            backend_proc.terminate()
        if frontend_proc:
            frontend_proc.terminate()
        print("[退出] ✅ 服务已停止")
        time.sleep(1)


if __name__ == "__main__":
    main()
