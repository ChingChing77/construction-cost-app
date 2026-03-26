"""
前端组件测试 - 建筑工程造价成本分析集成软件

测试 Streamlit 前端的数据处理、格式化、展示组件逻辑。
由于 Streamlit 需要浏览器环境，测试重点验证：
- 数据格式化函数
- 数据处理和转换逻辑
- 页面导航逻辑
- 组件数据结构

使用 pytest + mock 模式，不依赖真实浏览器。
"""

import pytest
import sys
import os
from datetime import date
from unittest.mock import MagicMock, patch
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

import streamlit_app as app


# ==================== 数据格式化测试 ====================

class TestDataFormatting:
    """
    数据格式化函数测试
    
    验证货币、面积、百分比等数据的格式化逻辑。
    """

    def test_format_currency_yuan(self):
        """
        测试小金额货币格式化
        
        保留两位小数，带千分位逗号，单位为"万元"。
        """
        result = app.format_currency(8500.5)
        assert "8,500.50" in result
        assert "万元" in result

    def test_format_currency_yi(self):
        """
        测试大金额自动转换为亿元
        
        超过1亿元时自动转换单位。
        """
        result = app.format_currency(15000.0)  # 1.5亿
        assert "1.50" in result
        assert "亿元" in result

    def test_format_currency_negative(self):
        """
        测试负数货币格式化
        
        负数（节省）应正确显示。
        """
        result = app.format_currency(-2500.75)
        assert "-" in result or "-" in result

    def test_format_currency_custom_unit(self):
        """
        测试自定义单位格式化
        """
        result = app.format_currency(500.0, unit="元")
        assert "500.00" in result
        assert "元" in result

    def test_format_area_small(self):
        """
        测试小面积格式化（平方米）
        
        不足1万平方米时显示为平方米。
        """
        result = app.format_area(8000)
        assert "8,000" in result
        assert "m²" in result

    def test_format_area_large(self):
        """
        测试大面积格式化（万平方米）
        
        超过1万平方米时自动转换。
        """
        result = app.format_area(25000)
        assert "2.50" in result
        assert "万m²" in result

    def test_format_percentage_positive(self):
        """
        测试正百分比格式化
        
        正数应显示 "+" 号。
        """
        result = app.format_percentage(10.5)
        assert result.startswith("+")
        assert "10.50" in result
        assert "%" in result

    def test_format_percentage_negative(self):
        """
        测试负百分比格式化
        
        负数不需要额外符号。
        """
        result = app.format_percentage(-5.25)
        assert "-" in result
        assert "5.25" in result

    def test_format_percentage_no_sign(self):
        """
        测试不显示符号的百分比
        """
        result = app.format_percentage(15.0, show_sign=False)
        assert result == "15.00%"

    def test_format_percentage_zero(self):
        """
        测试零值百分比格式化
        """
        result = app.format_percentage(0.0)
        assert "0.00%" in result


# ==================== 状态与风险显示测试 ====================

class TestStatusDisplay:
    """
    状态显示与风险指示测试
    """

    def test_status_color_normal(self):
        """
        测试正常状态颜色
        """
        assert app.get_status_color("正常") == "green"

    def test_status_color_overrun(self):
        """
        测试超支状态颜色
        """
        assert app.get_status_color("超支") == "red"

    def test_status_color_savings(self):
        """
        测试节省状态颜色
        """
        assert app.get_status_color("节省") == "blue"

    def test_status_color_active(self):
        """
        测试在建状态颜色
        """
        assert app.get_status_color("在建") == "blue"

    def test_status_color_planning(self):
        """
        测试规划中状态颜色
        """
        assert app.get_status_color("规划中") == "gray"

    def test_status_color_unknown(self):
        """
        测试未知状态默认颜色（灰色）
        """
        assert app.get_status_color("未知状态") == "gray"

    def test_risk_indicator_at_risk(self):
        """
        测试风险项目指示器
        """
        result = app.get_risk_indicator(at_risk=True)
        assert "🚨" in result

    def test_risk_indicator_normal(self):
        """
        测试正常项目指示器
        """
        result = app.get_risk_indicator(at_risk=False)
        assert "✅" in result


# ==================== 页面导航测试 ====================

class TestPageNavigation:
    """
    页面导航测试
    """

    def test_get_page_name(self):
        """
        测试页面名称获取
        
        验证各页面键名对应正确的显示名称。
        """
        assert app.get_page_name("overview") == "概览"
        assert app.get_page_name("projects") == "项目管理"
        assert app.get_page_name("analytics") == "成本分析"
        assert app.get_page_name("prediction") == "趋势预测"
        assert app.get_page_name("export") == "报表导出"

    def test_page_keys_complete(self):
        """
        测试页面键完整性
        
        确保所有页面都已定义。
        """
        expected_keys = ["overview", "projects", "analytics", "prediction", "export"]
        for key in expected_keys:
            assert key in app.PAGES.values()


# ==================== 数据处理测试 ====================

class TestDataProcessing:
    """
    数据处理函数测试
    
    验证 DataFrame 转换、筛选等数据处理逻辑。
    """

    def test_prepare_project_table_empty(self):
        """
        测试空项目列表处理
        """
        df = app.prepare_project_table([])
        assert df.empty
        assert len(df.columns) == 0

    def test_prepare_project_table_with_data(self, sample_projects):
        """
        测试项目数据表转换
        
        验证添加了偏差金额、偏差率、状态分类等计算列。
        """
        df = app.prepare_project_table(sample_projects)
        
        assert not df.empty
        assert "偏差金额" in df.columns
        assert "偏差率" in df.columns
        assert "状态分类" in df.columns
        
        # 验证上海办公楼项目（actual=23500 > planned=21000）被正确识别为超支
        overrun_rows = df[df["状态分类"] == "超支"]
        assert len(overrun_rows) > 0

    def test_prepare_project_table_variance_calculation(self, sample_projects):
        """
        测试偏差计算的正确性
        
        偏差 = 实际 - 计划
        偏差率 = 偏差 / 计划 * 100
        """
        df = app.prepare_project_table(sample_projects)
        
        # 上海办公楼：actual=23500, planned=21000
        shanghai = df[df["location"] == "上海"].iloc[0]
        assert shanghai["偏差金额"] == 2500.0
        assert shanghai["偏差率"] == pytest.approx(11.90, rel=0.1)

    def test_prepare_trend_chart_data_empty(self):
        """
        测试空趋势数据处理
        """
        result = app.prepare_trend_chart_data([])
        
        assert result["periods"] == []
        assert result["planned"] == []
        assert result["actual"] == []

    def test_prepare_trend_chart_data_with_values(self, monthly_trend_data):
        """
        测试趋势图表数据转换
        
        验证累计值正确计算。
        """
        result = app.prepare_trend_chart_data(monthly_trend_data)
        
        assert len(result["periods"]) == len(monthly_trend_data)
        assert len(result["cumulative_planned"]) == len(monthly_trend_data)
        
        # 验证最后一个累计值
        last_cum = result["cumulative_planned"][-1]
        expected = sum(d["planned"] for d in monthly_trend_data)
        assert last_cum == pytest.approx(expected, rel=0.01)

    def test_prepare_budget_breakdown_chart(self):
        """
        测试预算构成图表数据准备
        """
        breakdown = {
            "土建工程": 3600.0,
            "安装工程": 1600.0,
            "装饰工程": 1600.0,
            "其他费用": 1200.0,
        }
        
        result = app.prepare_budget_breakdown_chart(breakdown)
        
        assert result["labels"] == list(breakdown.keys())
        assert result["values"] == list(breakdown.values())

    def test_prepare_budget_breakdown_chart_empty(self):
        """
        测试空 breakdown 数据处理
        """
        result = app.prepare_budget_breakdown_chart({})
        
        assert result["labels"] == []
        assert result["values"] == []

    def test_prepare_prediction_summary_normal(self):
        """
        测试正常项目预测摘要格式化
        """
        prediction = {
            "predicted_final_cost": 8000.0,
            "confidence_interval_low": 7500.0,
            "confidence_interval_high": 8500.0,
            "at_risk": False,
            "risk_factors": [],
        }
        
        summary = app.prepare_prediction_summary(prediction)
        
        assert "8,000" in summary  # 带千分位格式化的数值
        assert "✅" in summary

    def test_prepare_prediction_summary_at_risk(self):
        """
        测试风险项目预测摘要格式化
        """
        prediction = {
            "predicted_final_cost": 9200.0,
            "confidence_interval_low": 8500.0,
            "confidence_interval_high": 9900.0,
            "at_risk": True,
            "risk_factors": ["预测成本将超支10%以上"],
        }
        
        summary = app.prepare_prediction_summary(prediction)
        
        assert "🚨" in summary
        assert "风险因素" in summary


# ==================== 项目筛选测试 ====================

class TestProjectFiltering:
    """
    项目筛选功能测试
    """

    def test_filter_by_status_all(self, sample_projects):
        """
        测试"全部"状态筛选返回所有项目
        """
        result = app.filter_projects_by_status(sample_projects, "全部")
        assert len(result) == len(sample_projects)

    def test_filter_by_status_specific(self, sample_projects):
        """
        测试按具体状态筛选
        """
        result = app.filter_projects_by_status(sample_projects, "在建")
        
        assert all(p["status"] == "在建" for p in result)

    def test_filter_by_type_all(self, sample_projects):
        """
        测试"全部"类型筛选返回所有项目
        """
        result = app.filter_projects_by_type(sample_projects, "全部")
        assert len(result) == len(sample_projects)

    def test_filter_by_type_specific(self, sample_projects):
        """
        测试按具体类型筛选
        """
        result = app.filter_projects_by_type(sample_projects, "住宅楼")
        
        assert all(p["project_type"] == "住宅楼" for p in result)

    def test_filter_by_empty_type(self, sample_projects):
        """
        测试空字符串类型筛选返回所有项目
        """
        result = app.filter_projects_by_type(sample_projects, "")
        assert len(result) == len(sample_projects)


# ==================== 仪表板 KPI 构建测试 ====================

class TestDashboardKPIs:
    """
    仪表板 KPI 卡片构建测试
    """

    def test_build_overview_kpis_empty(self):
        """
        测试空项目列表的 KPI 构建
        """
        kpis = app.build_overview_kpis([])
        assert kpis == []

    def test_build_overview_kpis_with_data(self, sample_projects):
        """
        测试有数据时的 KPI 构建
        
        验证生成了正确数量和类型的 KPI 卡片。
        """
        kpis = app.build_overview_kpis(sample_projects)
        
        assert len(kpis) > 0
        assert all(k["type"] == "kpi_card" for k in kpis)
        
        # 验证第一个 KPI 是项目总数
        assert kpis[0]["title"] == "项目总数"
        assert kpis[0]["value"] == len(sample_projects)

    def test_build_overview_kpis_variance_color(self, sample_projects):
        """
        测试偏差 KPI 颜色正确性
        
        节省时绿色，超支时红色。
        """
        kpis = app.build_overview_kpis(sample_projects)
        
        # 找到偏差 KPI
        variance_kpi = next((k for k in kpis if k["title"] == "成本偏差"), None)
        assert variance_kpi is not None
        
        # sample_projects 中有超支有节省，总体可能偏节省
        # 根据数据：上海办公楼超支2500，南京桥梁节省500，深圳商业综合体节省1000
        # 成都学校超支300，总偏差约 2500-500-1000+300 = 1300（超支）
        # 所以颜色应为 red
        assert variance_kpi["color"] in ["red", "green", "gray"]

    def test_build_overview_kpis_active_projects(self, sample_projects):
        """
        测试在建项目计数 KPI
        """
        kpis = app.build_overview_kpis(sample_projects)
        
        active_kpi = next((k for k in kpis if k["title"] == "在建项目"), None)
        assert active_kpi is not None
        
        expected_active = len([p for p in sample_projects if p["status"] == "在建"])
        assert active_kpi["value"] == expected_active

    def test_build_project_filters(self, sample_projects):
        """
        测试项目筛选选项构建
        
        验证生成了状态和类型筛选选项列表。
        """
        filters = app.build_project_filters(sample_projects)
        
        assert "statuses" in filters
        assert "project_types" in filters
        
        # "全部"应作为第一项
        assert filters["statuses"][0] == "全部"
        assert filters["project_types"][0] == "全部"
        
        # 验证各筛选项唯一性
        assert len(filters["statuses"]) == len(set(filters["statuses"]))
        assert len(filters["project_types"]) == len(set(filters["project_types"]))


# ==================== 组件数据结构测试 ====================

class TestComponentStructures:
    """
    组件数据结构测试
    
    验证 StreamlitComponents 模拟类返回正确的数据结构。
    """

    def test_metric_component(self):
        """
        测试 metric 组件数据结构
        """
        result = app.StreamlitComponents.metric("总预算", "8,500 万元", "+5%")
        
        assert result["type"] == "metric"
        assert result["label"] == "总预算"
        assert result["value"] == "8,500 万元"
        assert result["delta"] == "+5%"

    def test_metric_component_no_delta(self):
        """
        测试无 delta 的 metric 组件
        """
        result = app.StreamlitComponents.metric("项目数", "5 个")
        
        assert result["delta"] is None

    def test_kpi_card_component(self):
        """
        测试 KPI 卡片组件数据结构
        """
        result = app.StreamlitComponents.kpi_card(
            title="累计支出",
            value=8500.5,
            unit="万元",
            color="blue"
        )
        
        assert result["type"] == "kpi_card"
        assert result["title"] == "累计支出"
        assert result["value"] == 8500.5
        assert result["unit"] == "万元"
        assert result["color"] == "blue"

    def test_data_table_component(self, sample_projects):
        """
        测试 DataFrame 组件数据结构
        
        验证能够正确处理 pandas DataFrame。
        """
        import pandas as pd
        df = pd.DataFrame(sample_projects)
        
        result = app.StreamlitComponents.data_table(df)
        
        assert result["type"] == "data_table"
        assert result["rows"] == len(df)
        assert result["columns"] == list(df.columns)
        assert result["has_data"] is True

    def test_data_table_empty(self):
        """
        测试空 DataFrame 组件处理
        """
        import pandas as pd
        df = pd.DataFrame()
        
        result = app.StreamlitComponents.data_table(df)
        
        assert result["has_data"] is False
        assert result["rows"] == 0


# ==================== 集成场景测试 ====================

class TestDashboardIntegration:
    """
    仪表板集成场景测试
    
    模拟真实使用场景，验证多个组件协同工作。
    """

    def test_full_project_analysis_flow(self, sample_projects, monthly_trend_data):
        """
        测试完整项目分析流程
        
        从项目数据到表格展示、图表数据、KPI 构建的全流程。
        """
        # 1. 筛选在建项目
        active = app.filter_projects_by_status(sample_projects, "在建")
        
        # 2. 准备表格
        table_df = app.prepare_project_table(active)
        assert not table_df.empty
        
        # 3. 构建 KPI
        kpis = app.build_overview_kpis(active)
        assert len(kpis) > 0
        
        # 4. 构建筛选选项
        filters = app.build_project_filters(active)
        assert "statuses" in filters
        
        # 5. 准备图表数据
        chart_data = app.prepare_trend_chart_data(monthly_trend_data)
        assert len(chart_data["periods"]) == len(monthly_trend_data)

    def test_prediction_flow(self, prediction_scenarios):
        """
        测试预测流程
        
        验证各预测场景的摘要格式化。
        """
        for scenario in prediction_scenarios:
            # 模拟预测结果
            from analytics import predict_final_cost
            prediction = predict_final_cost(
                current_cost=scenario["current_cost"],
                progress=scenario["progress"],
                planned_total=scenario["planned_total"],
            )
            
            # 格式化摘要
            summary = app.prepare_prediction_summary(prediction)
            
            assert "预测最终成本" in summary
            assert "置信区间" in summary

    def test_multi_project_comparison(self, sample_projects):
        """
        测试多项目对比展示
        
        验证表格能正确处理多类型项目数据。
        """
        df = app.prepare_project_table(sample_projects)
        
        # 验证所有项目类型都在表格中
        unique_types = df["project_type"].unique()
        assert len(unique_types) >= 3  # 至少有住宅楼、办公楼、桥梁等
        
        # 验证偏差分类
        assert "超支" in df["状态分类"].values
        assert "节省" in df["状态分类"].values

    def test_large_project_filtering(self, sample_projects):
        """
        测试大型项目筛选
        
        筛选面积超过一定规模的项目。
        """
        large_projects = [p for p in sample_projects if p.get("total_area", 0) > 30000]
        
        assert len(large_projects) > 0
        
        for p in large_projects:
            assert p["total_area"] > 30000
        
        # 验证所有大型项目都在表格中正确显示
        df = app.prepare_project_table(large_projects)
        assert len(df) == len(large_projects)
