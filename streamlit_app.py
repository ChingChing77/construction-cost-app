"""
Streamlit 前端应用 - 建筑工程造价成本分析集成软件

提供数据仪表板、成本分析图表、项目管理界面。
由于 Streamlit 依赖浏览器环境，测试使用 stub 模式验证核心逻辑。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import List, Dict, Optional
import pandas as pd


# ==================== 页面导航 ====================

PAGES = {
    "概览": "overview",
    "项目管理": "projects",
    "成本分析": "analytics",
    "趋势预测": "prediction",
    "报表导出": "export",
}


def get_page_name(page_key: str) -> str:
    """
    获取页面显示名称
    
    Args:
        page_key: 页面键名
    
    Returns:
        页面中文显示名称
    """
    for name, key in PAGES.items():
        if key == page_key:
            return name
    return page_key


# ==================== 数据格式化函数（可测试部分） ====================

def format_currency(value: float, unit: str = "万元") -> str:
    """
    格式化货币数值显示
    
    Args:
        value: 数值
        unit: 单位（万元/亿元）
    
    Returns:
        格式化字符串，如 "8,500 万元"
    """
    if abs(value) >= 10000:
        return f"{value / 10000:.2f} 亿元"
    return f"{value:,.2f} {unit}"


def format_area(value: float) -> str:
    """
    格式化面积显示
    
    Args:
        value: 面积（平方米）
    
    Returns:
        格式化字符串，如 "2.5 万m²"
    """
    if abs(value) >= 10000:
        return f"{value / 10000:.2f} 万m²"
    return f"{value:,.0f} m²"


def format_percentage(value: float, show_sign: bool = True) -> str:
    """
    格式化百分比显示
    
    Args:
        value: 百分比值（如 10.5 表示 10.5%）
        show_sign: 是否显示正负符号
    
    Returns:
        格式化字符串，如 "+10.5%"
    """
    if show_sign and value > 0:
        return f"+{value:.2f}%"
    return f"{value:.2f}%"


def get_status_color(status: str) -> str:
    """
    获取状态对应的颜色代码
    
    Args:
        status: 状态值
    
    Returns:
        Streamlit 颜色代码
    """
    color_map = {
        "正常": "green",
        "超支": "red",
        "节省": "blue",
        "在建": "blue",
        "规划中": "gray",
        "收尾": "orange",
        "已完成": "green",
    }
    return color_map.get(status, "gray")


def get_risk_indicator(at_risk: bool) -> str:
    """
    获取风险指示器 emoji
    
    Args:
        at_risk: 是否存在风险
    
    Returns:
        风险指示器
    """
    return "🚨 风险项目" if at_risk else "✅ 正常"


# ==================== 数据处理函数（可测试部分） ====================

def prepare_project_table(projects: List[Dict]) -> pd.DataFrame:
    """
    准备项目数据表格
    
    将项目列表转换为 pandas DataFrame 用于 Streamlit 展示。
    
    Args:
        projects: 项目列表
    
    Returns:
        DataFrame 格式的项目数据
    """
    if not projects:
        return pd.DataFrame()
    
    df = pd.DataFrame(projects)
    
    # 添加计算列
    if "planned_cost" in df.columns and "actual_cost" in df.columns:
        df["偏差金额"] = df["actual_cost"] - df["planned_cost"]
        df["偏差率"] = ((df["偏差金额"] / df["planned_cost"]) * 100).round(2)
        
        def classify_variance(row):
            if row["偏差金额"] > 0:
                return "超支"
            elif row["偏差金额"] < 0:
                return "节省"
            return "正常"
        
        df["状态分类"] = df.apply(classify_variance, axis=1)
    
    return df


def prepare_trend_chart_data(monthly_data: List[Dict]) -> Dict:
    """
    准备趋势图表数据
    
    将月度数据转换为 Plotly 图表所需格式。
    
    Args:
        monthly_data: 月度趋势数据
    
    Returns:
        包含 periods, planned, actual, cumulative_planned, cumulative_actual 的字典
    """
    if not monthly_data:
        return {
            "periods": [],
            "planned": [],
            "actual": [],
            "cumulative_planned": [],
            "cumulative_actual": [],
        }
    
    periods = [d.get("period", "") for d in monthly_data]
    planned = [d.get("planned", 0) for d in monthly_data]
    actual = [d.get("actual", 0) for d in monthly_data]
    
    cumulative_planned = []
    cumulative_actual = []
    cp, ca = 0, 0
    for p, a in zip(planned, actual):
        cp += p
        ca += a
        cumulative_planned.append(round(cp, 2))
        cumulative_actual.append(round(ca, 2))
    
    return {
        "periods": periods,
        "planned": planned,
        "actual": actual,
        "cumulative_planned": cumulative_planned,
        "cumulative_actual": cumulative_actual,
    }


def prepare_budget_breakdown_chart(breakdown: Dict) -> Dict:
    """
    准备预算构成图表数据
    
    Args:
        breakdown: 成本分解字典
    
    Returns:
        适合绘制饼图的数据
    """
    if not breakdown:
        return {"labels": [], "values": []}
    
    labels = list(breakdown.keys())
    values = list(breakdown.values())
    
    return {"labels": labels, "values": values}


def prepare_prediction_summary(prediction: Dict) -> str:
    """
    格式化预测结果摘要
    
    Args:
        prediction: 预测结果字典
    
    Returns:
        格式化的摘要文本
    """
    predicted = prediction.get("predicted_final_cost", 0)
    low = prediction.get("confidence_interval_low", 0)
    high = prediction.get("confidence_interval_high", 0)
    at_risk = prediction.get("at_risk", False)
    risk_factors = prediction.get("risk_factors", [])
    
    summary_lines = [
        f"预测最终成本：{format_currency(predicted)}",
        f"置信区间：{format_currency(low)} ~ {format_currency(high)}",
        f"项目风险状态：{get_risk_indicator(at_risk)}",
    ]
    
    if risk_factors:
        summary_lines.append("风险因素：")
        for factor in risk_factors:
            summary_lines.append(f"  • {factor}")
    
    return "\n".join(summary_lines)


def filter_projects_by_status(projects: List[Dict], status: str) -> List[Dict]:
    """
    按状态筛选项目
    
    Args:
        projects: 项目列表
        status: 状态筛选条件
    
    Returns:
        筛选后的项目列表
    """
    if status == "全部":
        return projects
    return [p for p in projects if p.get("status") == status]


def filter_projects_by_type(projects: List[Dict], ptype: str) -> List[Dict]:
    """
    按类型筛选项目
    
    Args:
        projects: 项目列表
        ptype: 类型筛选条件
    
    Returns:
        筛选后的项目列表
    """
    if ptype == "全部" or ptype == "":
        return projects
    return [p for p in projects if p.get("project_type") == ptype]


# ==================== 模拟 Streamlit 组件行为 ====================

class StreamlitComponents:
    """
    Streamlit 组件行为模拟类
    
    提供与 Streamlit 组件对应的一致性接口用于测试。
    """
    
    @staticmethod
    def metric(label: str, value: str, delta: Optional[str] = None):
        """
        模拟 st.metric 组件
        
        返回包含标签、数值、变化量的字典。
        """
        return {
            "type": "metric",
            "label": label,
            "value": value,
            "delta": delta,
        }
    
    @staticmethod
    def kpi_card(title: str, value: float, unit: str, color: str) -> Dict:
        """
        模拟 KPI 卡片组件
        
        Args:
            title: 卡片标题
            value: 数值
            unit: 单位
            color: 颜色（green/red/blue/gray）
        
        Returns:
            KPI 卡片数据字典
        """
        return {
            "type": "kpi_card",
            "title": title,
            "value": value,
            "unit": unit,
            "color": color,
        }
    
    @staticmethod
    def data_table(df: pd.DataFrame, max_rows: int = 100) -> Dict:
        """
        模拟 st.dataframe 组件
        
        验证 DataFrame 结构并返回描述字典。
        """
        return {
            "type": "data_table",
            "rows": min(len(df), max_rows),
            "columns": list(df.columns),
            "has_data": len(df) > 0,
        }


# ==================== 仪表板页面构建逻辑 ====================

def build_overview_kpis(projects: List[Dict]) -> List[Dict]:
    """
    构建概览页 KPI 卡片数据
    
    Args:
        projects: 项目列表
    
    Returns:
        KPI 卡片列表
    """
    if not projects:
        return []
    
    total_budget = sum(p.get("budget", 0) for p in projects)
    total_actual = sum(p.get("actual_cost", 0) for p in projects)
    total_planned = sum(p.get("planned_cost", 0) for p in projects)
    
    overrun_projects = [p for p in projects if p.get("actual_cost", 0) > p.get("planned_cost", 0)]
    active_projects = [p for p in projects if p.get("status") == "在建"]
    
    kpis = [
        StreamlitComponents.kpi_card(
            "项目总数", len(projects), "个", "blue"
        ),
        StreamlitComponents.kpi_card(
            "总预算", total_budget, "万元", "blue"
        ),
        StreamlitComponents.kpi_card(
            "累计实际支出", total_actual, "万元", "blue"
        ),
        StreamlitComponents.kpi_card(
            "在建项目", len(active_projects), "个", "green"
        ),
    ]
    
    # 成本偏差
    variance = total_actual - total_planned
    variance_color = "red" if variance > 0 else "green" if variance < 0 else "gray"
    kpis.append(StreamlitComponents.kpi_card(
        "成本偏差", variance, "万元", variance_color
    ))
    
    # 超支项目数
    kpis.append(StreamlitComponents.kpi_card(
        "超支项目", len(overrun_projects), "个", "red" if overrun_projects else "green"
    ))
    
    return kpis


def build_project_filters(projects: List[Dict]) -> Dict[str, List]:
    """
    构建项目筛选选项
    
    Args:
        projects: 项目列表
    
    Returns:
        包含各筛选选项的字典
    """
    statuses = sorted(set(p.get("status", "未知") for p in projects))
    statuses.insert(0, "全部")
    
    types = sorted(set(p.get("project_type", "其他") for p in projects))
    types.insert(0, "全部")
    
    return {
        "statuses": statuses,
        "project_types": types,
    }
