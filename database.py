# -*- coding: utf-8 -*-
"""
数据库模块 - SQLite 数据库操作
负责表创建、CRUD 操作及数据初始化
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(__file__), "construction_cost.db")


def get_connection() -> sqlite3.Connection:
    """获取数据库连接（线程局部使用）"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
    return conn


def init_database():
    """初始化数据库表结构"""
    conn = get_connection()
    cursor = conn.cursor()

    # 项目表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location TEXT,
            total_budget REAL DEFAULT 0.0,
            total_actual REAL DEFAULT 0.0,
            status TEXT DEFAULT 'planning',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # 成本明细表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            cost_type TEXT NOT NULL,
            budget_cost REAL DEFAULT 0.0,
            actual_cost REAL DEFAULT 0.0,
            variance_analysis TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    # 月度成本趋势表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS monthly_costs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            month TEXT NOT NULL,
            planned_cost REAL DEFAULT 0.0,
            actual_cost REAL DEFAULT 0.0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


def init_sample_data():
    """初始化示例数据（仅在数据为空时调用）"""
    conn = get_connection()
    cursor = conn.cursor()

    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 插入示例项目
    cursor.execute("""
        INSERT INTO projects (name, description, location, total_budget, total_actual, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "城市综合体建设项目",
        "集商业、办公、住宅于一体的城市综合体项目",
        "北京市朝阳区",
        50000000.0,
        32500000.0,
        "ongoing",
        now,
        now
    ))
    project_id = cursor.lastrowid

    # 插入成本明细
    cost_items = [
        ("土建工程", 15000000.0, 14500000.0, "节省 3.3%，进度正常"),
        ("机电安装", 10000000.0, 8200000.0, "节省 18%，材料价格下跌"),
        ("室内装修", 8000000.0, 6500000.0, "节省 18.75%，设计方案优化"),
        ("景观绿化", 3000000.0, 3100000.0, "超支 3.3%，苗木价格上涨"),
        ("其他费用", 14000000.0, 200000.0, "待支付"),
    ]
    for cost_type, budget, actual, variance in cost_items:
        cursor.execute("""
            INSERT INTO cost_items (project_id, cost_type, budget_cost, actual_cost, variance_analysis, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id, cost_type, budget, actual, variance, now, now))

    # 插入月度趋势数据（近12个月）
    months = [
        "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09",
        "2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03"
    ]
    planned = [280000, 320000, 380000, 420000, 480000, 520000,
               560000, 600000, 650000, 680000, 720000, 750000]
    actual = [260000, 310000, 360000, 400000, 470000, 510000,
              540000, 590000, 630000, 660000, 700000, 730000]
    for month, p, a in zip(months, planned, actual):
        cursor.execute("""
            INSERT INTO monthly_costs (project_id, month, planned_cost, actual_cost, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, month, p, a, now))

    # 第二个示例项目
    cursor.execute("""
        INSERT INTO projects (name, description, location, total_budget, total_actual, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "住宅小区项目",
        "高档住宅小区，包含12栋住宅楼及配套商业",
        "上海市浦东新区",
        80000000.0,
        48000000.0,
        "ongoing",
        now,
        now
    ))
    project_id2 = cursor.lastrowid

    cost_items2 = [
        ("土建工程", 25000000.0, 24800000.0, "节省 0.8%，基本持平"),
        ("机电安装", 15000000.0, 13500000.0, "节省 10%，设备集中采购"),
        ("景观绿化", 5000000.0, 5200000.0, "超支 4%，设计变更"),
    ]
    for cost_type, budget, actual, variance in cost_items2:
        cursor.execute("""
            INSERT INTO cost_items (project_id, cost_type, budget_cost, actual_cost, variance_analysis, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (project_id2, cost_type, budget, actual, variance, now, now))

    conn.commit()
    conn.close()
    print("[DB] 示例数据初始化完成")


# ============ 项目 CRUD ============

def create_project(name: str, description: str = "", location: str = "",
                   total_budget: float = 0.0, total_actual: float = 0.0,
                   status: str = "planning") -> int:
    """创建项目，返回新项目ID"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO projects (name, description, location, total_budget, total_actual, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (name, description, location, total_budget, total_actual, status, now, now))
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def get_all_projects() -> List[Dict[str, Any]]:
    """获取所有项目列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, description, location, total_budget, total_actual,
               status, created_at, updated_at
        FROM projects ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_project_by_id(project_id: int) -> Optional[Dict[str, Any]]:
    """根据ID获取单个项目"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name, description, location, total_budget, total_actual,
               status, created_at, updated_at
        FROM projects WHERE id = ?
    """, (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_project(project_id: int, name: str = None, description: str = None,
                   location: str = None, total_budget: float = None,
                   total_actual: float = None, status: str = None) -> bool:
    """更新项目信息，返回是否成功"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fields = []
    values = []
    if name is not None:
        fields.append("name = ?")
        values.append(name)
    if description is not None:
        fields.append("description = ?")
        values.append(description)
    if location is not None:
        fields.append("location = ?")
        values.append(location)
    if total_budget is not None:
        fields.append("total_budget = ?")
        values.append(total_budget)
    if total_actual is not None:
        fields.append("total_actual = ?")
        values.append(total_actual)
    if status is not None:
        fields.append("status = ?")
        values.append(status)

    if not fields:
        return False

    fields.append("updated_at = ?")
    values.append(now)
    values.append(project_id)

    cursor.execute(f"UPDATE projects SET {', '.join(fields)} WHERE id = ?", values)
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_project(project_id: int) -> bool:
    """删除项目，返回是否成功"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ============ 成本明细 CRUD ============

def get_cost_items_by_project(project_id: int) -> List[Dict[str, Any]]:
    """获取项目的成本明细列表"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, project_id, cost_type, budget_cost, actual_cost,
               variance_analysis, created_at, updated_at
        FROM cost_items WHERE project_id = ? ORDER BY id
    """, (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_cost_item(project_id: int, cost_type: str, budget_cost: float = 0.0,
                  actual_cost: float = 0.0, variance_analysis: str = "") -> int:
    """添加成本明细"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO cost_items (project_id, cost_type, budget_cost, actual_cost, variance_analysis, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (project_id, cost_type, budget_cost, actual_cost, variance_analysis, now, now))
    pid = cursor.lastrowid
    conn.commit()
    conn.close()
    return pid


def update_cost_item(item_id: int, cost_type: str = None, budget_cost: float = None,
                     actual_cost: float = None, variance_analysis: str = None) -> bool:
    """更新成本明细"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fields = []
    values = []
    if cost_type is not None:
        fields.append("cost_type = ?")
        values.append(cost_type)
    if budget_cost is not None:
        fields.append("budget_cost = ?")
        values.append(budget_cost)
    if actual_cost is not None:
        fields.append("actual_cost = ?")
        values.append(actual_cost)
    if variance_analysis is not None:
        fields.append("variance_analysis = ?")
        values.append(variance_analysis)
    if not fields:
        return False
    fields.append("updated_at = ?")
    values.append(now)
    values.append(item_id)
    cursor.execute(f"UPDATE cost_items SET {', '.join(fields)} WHERE id = ?", values)
    updated = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return updated


def delete_cost_item(item_id: int) -> bool:
    """删除成本明细"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cost_items WHERE id = ?", (item_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


# ============ 月度趋势数据 ============

def get_monthly_costs_by_project(project_id: int) -> List[Dict[str, Any]]:
    """获取项目月度成本趋势"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, project_id, month, planned_cost, actual_cost, created_at
        FROM monthly_costs WHERE project_id = ? ORDER BY month
    """, (project_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_monthly_costs() -> List[Dict[str, Any]]:
    """获取所有项目月度成本趋势（汇总）"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, project_id, month, planned_cost, actual_cost, created_at
        FROM monthly_costs ORDER BY month
    """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ============ 统计汇总 ============

def get_dashboard_stats() -> Dict[str, Any]:
    """获取仪表盘统计数据"""
    conn = get_connection()
    cursor = conn.cursor()

    # 项目总数
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]

    # 各状态项目数
    cursor.execute("SELECT status, COUNT(*) FROM projects GROUP BY status")
    status_counts = {row[0]: row[1] for row in cursor.fetchall()}

    # 总预算和总实际成本
    cursor.execute("SELECT SUM(total_budget), SUM(total_actual) FROM projects")
    row = cursor.fetchone()
    total_budget = row[0] or 0.0
    total_actual = row[1] or 0.0

    # 成本节约/超支
    cost_saved = total_budget - total_actual
    cost_saved_rate = (cost_saved / total_budget * 100) if total_budget > 0 else 0

    # 在建项目数
    cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'ongoing'")
    ongoing_projects = cursor.fetchone()[0]

    # 各成本类型的汇总（用于图表）
    cursor.execute("""
        SELECT cost_type,
               SUM(budget_cost) as total_budget,
               SUM(actual_cost) as total_actual
        FROM cost_items GROUP BY cost_type
    """)
    cost_type_summary = []
    for row in cursor.fetchall():
        cost_type_summary.append({
            "cost_type": row[0],
            "budget": row[1] or 0.0,
            "actual": row[2] or 0.0,
            "variance": (row[1] or 0.0) - (row[2] or 0.0)
        })

    conn.close()

    return {
        "total_projects": total_projects,
        "status_counts": status_counts,
        "ongoing_projects": ongoing_projects,
        "total_budget": total_budget,
        "total_actual": total_actual,
        "cost_saved": cost_saved,
        "cost_saved_rate": round(cost_saved_rate, 2),
        "cost_type_summary": cost_type_summary
    }


def get_cost_analysis() -> Dict[str, Any]:
    """获取成本分析数据"""
    conn = get_connection()
    cursor = conn.cursor()

    # 各项目成本分析
    cursor.execute("""
        SELECT p.id, p.name, p.total_budget, p.total_actual, p.status,
               SUM(ci.budget_cost) as sum_budget,
               SUM(ci.actual_cost) as sum_actual
        FROM projects p
        LEFT JOIN cost_items ci ON p.id = ci.project_id
        GROUP BY p.id
    """)
    project_costs = []
    for row in cursor.fetchall():
        budget = row[5] or 0.0
        actual = row[6] or 0.0
        variance = budget - actual
        variance_rate = (variance / budget * 100) if budget > 0 else 0
        project_costs.append({
            "project_id": row[0],
            "project_name": row[1],
            "total_budget": row[2],
            "total_actual": row[3],
            "sum_budget": budget,
            "sum_actual": actual,
            "variance": variance,
            "variance_rate": round(variance_rate, 2),
            "status": row[4]
        })

    # 成本类型分布（饼图数据）
    cursor.execute("""
        SELECT cost_type, SUM(actual_cost) as total
        FROM cost_items GROUP BY cost_type ORDER BY total DESC
    """)
    cost_distribution = [{"name": row[0], "value": row[1] or 0.0} for row in cursor.fetchall()]

    # 整体预算执行率
    cursor.execute("SELECT SUM(total_budget), SUM(total_actual) FROM projects")
    row = cursor.fetchone()
    total_budget = row[0] or 0.0
    total_actual = row[1] or 0.0
    execution_rate = (total_actual / total_budget * 100) if total_budget > 0 else 0

    conn.close()

    return {
        "project_costs": project_costs,
        "cost_distribution": cost_distribution,
        "execution_rate": round(execution_rate, 2),
        "total_budget": total_budget,
        "total_actual": total_actual
    }


def get_home_data() -> Dict[str, Any]:
    """生成首页综合数据（census/line/table 三板块）"""
    conn = get_connection()
    cursor = conn.cursor()

    # --- Census 统计卡片 ---
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(total_budget) FROM projects")
    total_budget = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT SUM(total_actual) FROM projects")
    total_actual = cursor.fetchone()[0] or 0.0

    cursor.execute("SELECT COUNT(*) FROM projects WHERE status = 'ongoing'")
    ongoing = cursor.fetchone()[0]

    # 整体预算执行率
    execution_rate = round((total_actual / total_budget * 100), 2) if total_budget > 0 else 0

    census = [
        [
            {"name": "项目总数", "value": float(total_projects)},
            {"name": "在建项目", "value": float(ongoing)},
        ],
        [
            {"name": "总预算（万元）", "value": round(total_budget / 10000, 2)},
            {"name": "总实际（万元）", "value": round(total_actual / 10000, 2)},
        ],
        [
            {"name": "预算执行率", "value": execution_rate},
            {"name": "成本节约（万元）", "value": round((total_budget - total_actual) / 10000, 2)},
        ]
    ]

    # --- Line 折线图（近12个月趋势） ---
    cursor.execute("""
        SELECT month,
               SUM(planned_cost) as planned,
               SUM(actual_cost) as actual
        FROM monthly_costs
        GROUP BY month
        ORDER BY month
    """)
    monthly_rows = cursor.fetchall()

    if monthly_rows:
        labels = [row[0] for row in monthly_rows]
        planned_data = [row[1] or 0.0 for row in monthly_rows]
        actual_data = [row[2] or 0.0 for row in monthly_rows]
    else:
        # 无数据时使用默认标签
        labels = ["2026-01", "2026-02", "2026-03"]
        planned_data = [0.0, 0.0, 0.0]
        actual_data = [0.0, 0.0, 0.0]

    line = [
        {
            "title": {"text": "月度成本趋势分析"},
            "labels": labels,
            "description": "计划成本 vs 实际成本（单位：元）",
            "datasets": [
                {"label": "计划成本", "data": planned_data},
                {"label": "实际成本", "data": actual_data},
            ],
            "unit": "元"
        }
    ]

    # --- Table 成本明细表 ---
    cursor.execute("""
        SELECT p.name as project_name,
               ci.cost_type,
               ci.budget_cost,
               ci.actual_cost,
               ci.variance_analysis
        FROM cost_items ci
        JOIN projects p ON ci.project_id = p.id
        ORDER BY p.name, ci.id
    """)
    table_rows = cursor.fetchall()

    table_header = [
        {"text": "项目名称", "value": "projectName"},
        {"text": "成本类型", "value": "costType"},
        {"text": "预算成本", "value": "budgetCost"},
        {"text": "实际成本", "value": "actualCost"},
        {"text": "差异分析", "value": "varianceAnalysis"},
    ]

    table_data = [
        {
            "projectName": row[0],
            "costType": row[1],
            "budgetCost": f"¥{row[2]:,.2f}",
            "actualCost": f"¥{row[3]:,.2f}",
            "varianceAnalysis": row[4] or "",
        }
        for row in table_rows
    ]

    table = [
        {
            "tableHeader": table_header,
            "tableData": table_data,
            "description": "各项目成本明细及差异分析",
            "button": "查看详情"
        }
    ]

    conn.close()

    return {
        "census": census,
        "line": line,
        "table": table
    }
