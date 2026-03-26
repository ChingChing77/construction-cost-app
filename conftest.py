"""
pytest 配置与 fixtures - 建筑工程造价成本分析集成软件测试套件

提供测试所需的数据库模拟、HTTP客户端、模拟数据等 fixture
"""

import pytest
import sys
import os
from typing import Dict, List
from datetime import date, timedelta
from fastapi.testclient import TestClient

# 确保项目模块在路径中
sys.path.insert(0, os.path.dirname(__file__))

from main import app


# ==================== 测试客户端 Fixture ====================

@pytest.fixture
def client():
    """
    FastAPI 测试客户端 fixture
    
    提供一个 TestClient 实例，用于测试 API 端点。
    每次测试后重置内存数据库状态。
    """
    with TestClient(app) as c:
        yield c
    # 测试后清理（如有需要）


# ==================== 模拟项目数据 Fixtures ====================

@pytest.fixture
def sample_projects() -> List[Dict]:
    """
    模拟建筑项目数据 fixture
    
    包含5个真实感极强的建筑项目，涵盖不同类型和地区。
    """
    return [
        {
            "id": 101,
            "name": "北京朝阳区高层住宅楼项目",
            "project_type": "住宅楼",
            "location": "北京",
            "total_area": 25000,
            "budget": 8500.0,
            "planned_cost": 8000.0,
            "actual_cost": 7850.0,
            "progress": 75.0,
            "start_date": "2023-06-01",
            "expected_end_date": "2024-12-31",
            "status": "在建",
        },
        {
            "id": 102,
            "name": "上海浦东新区甲级写字楼项目",
            "project_type": "办公楼",
            "location": "上海",
            "total_area": 42000,
            "budget": 22000.0,
            "planned_cost": 21000.0,
            "actual_cost": 23500.0,  # 超支
            "progress": 60.0,
            "start_date": "2023-03-15",
            "expected_end_date": "2025-06-30",
            "status": "在建",
        },
        {
            "id": 103,
            "name": "南京长江大桥加固维修工程",
            "project_type": "桥梁",
            "location": "南京",
            "total_area": 0,
            "budget": 12000.0,
            "planned_cost": 11500.0,
            "actual_cost": 11000.0,  # 节省
            "progress": 90.0,
            "start_date": "2022-09-01",
            "expected_end_date": "2024-03-31",
            "status": "收尾",
        },
        {
            "id": 104,
            "name": "深圳南山商业综合体项目",
            "project_type": "商业综合体",
            "location": "深圳",
            "total_area": 85000,
            "budget": 55000.0,
            "planned_cost": 52000.0,
            "actual_cost": 51000.0,  # 节省
            "progress": 45.0,
            "start_date": "2024-01-01",
            "expected_end_date": "2026-12-31",
            "status": "在建",
        },
        {
            "id": 105,
            "name": "成都天府新区公立学校新建项目",
            "project_type": "学校",
            "location": "成都",
            "total_area": 32000,
            "budget": 12000.0,
            "planned_cost": 11500.0,
            "actual_cost": 11800.0,  # 超支
            "progress": 30.0,
            "start_date": "2024-03-01",
            "expected_end_date": "2025-09-01",
            "status": "在建",
        },
        {
            "id": 106,
            "name": "武汉光谷大数据中心厂房项目",
            "project_type": "工业厂房",
            "location": "武汉",
            "total_area": 18000,
            "budget": 4500.0,
            "planned_cost": 4300.0,
            "actual_cost": 4400.0,
            "progress": 55.0,
            "start_date": "2023-11-01",
            "expected_end_date": "2025-02-28",
            "status": "在建",
        },
    ]


@pytest.fixture
def residential_project() -> Dict:
    """
    住宅楼项目 fixture（单项目测试用）
    """
    return {
        "name": "测试住宅楼项目",
        "project_type": "住宅楼",
        "location": "北京",
        "total_area": 15000,
        "budget": 5000.0,
        "planned_cost": 4750.0,
        "actual_cost": 4600.0,
        "progress": 65.0,
        "start_date": "2024-01-15",
        "expected_end_date": "2025-06-30",
        "status": "在建",
    }


@pytest.fixture
def office_project() -> Dict:
    """
    办公楼项目 fixture（单项目测试用）
    """
    return {
        "name": "测试办公楼项目",
        "project_type": "办公楼",
        "location": "上海",
        "total_area": 30000,
        "budget": 15000.0,
        "planned_cost": 14200.0,
        "actual_cost": 15000.0,  # 超支
        "progress": 50.0,
        "start_date": "2023-09-01",
        "expected_end_date": "2025-12-31",
        "status": "在建",
    }


@pytest.fixture
def bridge_project() -> Dict:
    """
    桥梁工程项目 fixture（单项目测试用）
    """
    return {
        "name": "测试桥梁工程项目",
        "project_type": "桥梁",
        "location": "南京",
        "total_area": 0,  # 桥梁按延米计算
        "budget": 8000.0,
        "planned_cost": 7600.0,
        "actual_cost": 7200.0,  # 节省
        "progress": 80.0,
        "start_date": "2023-04-01",
        "expected_end_date": "2024-10-31",
        "status": "收尾",
    }


# ==================== 成本明细数据 Fixture ====================

@pytest.fixture
def cost_items() -> List[Dict]:
    """
    成本明细科目 fixture
    
    模拟一个住宅楼项目的详细成本科目数据。
    """
    return [
        {
            "item_name": "土建主体结构",
            "category": "土建",
            "planned_cost": 2800.0,
            "actual_cost": 2750.0,
            "unit_price": 2100.0,
            "quantity": 12000,
            "progress": 85.0,
        },
        {
            "item_name": "机电安装工程",
            "category": "安装",
            "planned_cost": 1200.0,
            "actual_cost": 1150.0,
            "unit_price": 600.0,
            "quantity": 20000,
            "progress": 60.0,
        },
        {
            "item_name": "室内装修工程",
            "category": "装饰",
            "planned_cost": 1100.0,
            "actual_cost": 1050.0,
            "unit_price": 1100.0,
            "quantity": 10000,
            "progress": 45.0,
        },
        {
            "item_name": "室外附属工程",
            "category": "其他",
            "planned_cost": 500.0,
            "actual_cost": 480.0,
            "unit_price": 200.0,
            "quantity": 2500,
            "progress": 30.0,
        },
    ]


# ==================== 趋势分析数据 Fixture ====================

@pytest.fixture
def monthly_trend_data() -> List[Dict]:
    """
    月度趋势数据 fixture
    
    模拟项目12个月的计划成本与实际成本数据。
    """
    months = [
        "2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06",
        "2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
    ]
    planned_base = 600.0
    actual_base = 580.0
    data = []
    for i, month in enumerate(months):
        # 计划成本线性增长
        planned = planned_base * (i + 1)
        # 实际成本有波动（7-9月因雨季略高）
        if 6 <= i <= 8:
            actual = actual_base * (i + 1) * 1.08
        else:
            actual = actual_base * (i + 1) * 0.98
        data.append({
            "period": month,
            "planned": round(planned, 2),
            "actual": round(actual, 2),
        })
    return data


# ==================== 预测数据 Fixture ====================

@pytest.fixture
def prediction_scenarios() -> List[Dict]:
    """
    成本预测场景 fixture
    
    包含多个不同进度阶段的预测场景。
    """
    return [
        {
            "description": "项目初期（进度15%）",
            "current_cost": 1200.0,
            "progress": 15.0,
            "planned_total": 8000.0,
        },
        {
            "description": "项目中段（进度50%）",
            "current_cost": 4100.0,
            "progress": 50.0,
            "planned_total": 8000.0,
        },
        {
            "description": "项目后期（进度85%）",
            "current_cost": 7200.0,
            "progress": 85.0,
            "planned_total": 8000.0,
        },
        {
            "description": "超支项目（进度60%）",
            "current_cost": 5400.0,
            "progress": 60.0,
            "planned_total": 8000.0,
        },
    ]


# ==================== pytest 配置钩子 ====================

def pytest_configure(config):
    """pytest 全局配置钩子"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers", "api: API 端点测试"
    )
    config.addinivalue_line(
        "markers", "analytics: 数据分析模块测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
