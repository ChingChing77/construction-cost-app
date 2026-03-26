"""
配置文件 - 建筑工程造价成本分析集成软件
"""

import os
from pathlib import Path

# ============ 项目根目录 ============
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# ============ 数据库配置 ============
DB_PATH = DATA_DIR / "construction_cost.db"
DB_POOL_SIZE = 10
DB_MAX_OVERFLOW = 20

# ============ API 服务配置 ============
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True
API_WORKERS = 1

# ============ Streamlit 前端配置 ============
STREAMLIT_SERVER_PORT = 8501
STREAMLIT_SERVER_ADDRESS = "0.0.0.0"
STREAMLIT_BROWSER_GATHER_USAGE_STATS = False
STREAMLIT_SERVER_HEADLESS = True

# ============ 日志配置 ============
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILE = LOG_DIR / "app.log"
LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5

# ============ 其他配置 ============
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
