# 建筑工程造价成本分析集成软件

## 项目简介

建筑工程造价成本分析集成软件是一款面向工程建筑领域的数据分析平台，支持造价数据的导入、清洗、统计分析和可视化展示。系统采用 FastAPI 后端 + Streamlit 前端架构，便于部署和二次开发。

---

## 功能列表

- 📊 **数据导入** — 支持 Excel（.xlsx）批量导入造价数据
- 🔍 **数据清洗** — 自动处理缺失值、异常值，标准化字段
- 📈 **成本分析** — 分部分项工程成本统计、环比/同比分析
- 📉 **可视化图表** — 折线图、柱状图、饼图等交互图表（Plotly）
- 🌐 **RESTful API** — 提供数据查询、统计分析接口
- 🎨 **Web 前端** — Streamlit 交互式界面，操作简便

---

## 技术架构

```
┌─────────────────────────────────┐
│      Streamlit Frontend         │
│      (Port 8501)                │
└──────────────┬──────────────────┘
               │ HTTP / JSON
┌──────────────▼──────────────────┐
│      FastAPI Backend            │
│      (Port 8000)                │
│  ├── 数据处理模块               │
│  ├── 分析引擎                   │
│  └── API 路由                   │
└──────────────┬──────────────────┘
               │
┌──────────────▼──────────────────┐
│      SQLite Database            │
│   (construction_cost.db)        │
└─────────────────────────────────┘
```

| 技术栈 | 说明 |
|---|---|
| FastAPI | 高性能 Web 框架 |
| Uvicorn | ASGI 服务器 |
| Streamlit | 数据可视化前端框架 |
| Pandas | 数据处理与分析 |
| Plotly | 交互式图表 |
| Pydantic | 数据验证与模型 |
| SQLite | 轻量级数据库 |

---

## 目录结构

```
construction_cost/
├── config.py           # 全局配置文件
├── requirements.txt    # Python 依赖列表
├── main.py             # FastAPI 后端入口
├── streamlit_app.py    # Streamlit 前端入口
├── run_backend.sh      # 启动后端脚本
├── run_frontend.sh     # 启动前端脚本
├── README.md           # 项目说明文档
├── data/               # 数据存储目录（数据库文件）
│   └── .gitkeep
└── logs/               # 日志目录
    └── .gitkeep
```

---

## 安装部署步骤

### 环境要求

- Python >= 3.9
- Linux / macOS / Windows

### 1. 克隆 / 进入项目目录

```bash
cd /home/ubuntu/.openclaw/workspace/construction_cost
```

### 2. 创建虚拟环境（推荐）

```bash
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动后端服务

```bash
chmod +x run_backend.sh
./run_backend.sh
```

后端启动后运行在 `http://0.0.0.0:8000`，访问 `/docs` 查看 API 文档。

### 5. 启动前端服务

```bash
chmod +x run_frontend.sh
./run_frontend.sh
```

前端启动后访问 `http://<服务器IP>:8501`

### 6. 使用 systemd 管理服务（可选）

```ini
# /etc/systemd/system/construction-cost-backend.service
[Unit]
Description=Construction Cost Backend
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/.openclaw/workspace/construction_cost
ExecStart=/home/ubuntu/.openclaw/workspace/construction_cost/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 配置文件说明

`config.py` 中主要配置项：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `DB_PATH` | `data/construction_cost.db` | SQLite 数据库路径 |
| `API_HOST` | `0.0.0.0` | 后端监听地址 |
| `API_PORT` | `8000` | 后端监听端口 |
| `STREAMLIT_SERVER_PORT` | `8501` | 前端监听端口 |
| `LOG_LEVEL` | `INFO` | 日志级别 |
| `DEBUG` | `false` | 调试模式 |

生产环境请修改 `SECRET_KEY` 并设置 `DEBUG=false`。

---

## 常见问题

**Q: 数据库文件不存在？**  
A: 首次运行后端会自动创建 `data/construction_cost.db`。

**Q: 端口被占用？**  
A: 修改 `config.py` 中的 `API_PORT` 或 `STREAMLIT_SERVER_PORT`。

**Q: 日志在哪里？**  
A: 日志写入 `logs/app.log`，支持自动轮转（最大 10MB，保留 5 份）。
