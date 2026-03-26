"""
数据分析模块测试 - 建筑工程造价成本分析集成软件

测试 analytics.py 中所有核心分析函数的正确性：
- 成本计算
- 成本汇总
- 超支检测
- 趋势分析
- 成本预测
- 项目评分
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from analytics import (
    calculate_cost, summarize_costs, detect_overruns,
    analyze_trend, predict_final_cost, calculate_project_score,
    get_unit_price, get_region_coefficient,
)


# ==================== 成本计算测试 ====================

class TestCostCalculation:
    """
    成本计算函数测试
    
    验证不同建筑类型、地区的单价计算和成本估算。
    """

    def test_unit_price_residential_default_region(self):
        """
        测试默认地区住宅楼单价
        
        使用基准价：2800 元/m²
        """
        price = get_unit_price("住宅楼", "默认")
        assert price == 2800.0

    def test_unit_price_office_beijing(self):
        """
        测试北京办公楼单价
        
        北京系数 1.35，基准价 4200 元/m²
        期望：4200 * 1.35 = 5670
        """
        price = get_unit_price("办公楼", "北京")
        assert price == 5670.0

    def test_unit_price_office_shanghai(self):
        """
        测试上海办公楼单价
        
        上海系数 1.32，基准价 4200 元/m²
        期望：4200 * 1.32 = 5544
        """
        price = get_unit_price("办公楼", "上海")
        assert price == 5544.0

    def test_unit_price_commercial_shenzhen(self):
        """
        测试深圳商业综合体单价
        
        深圳系数 1.28，基准价 5500 元/m²
        期望：5500 * 1.28 = 7040
        """
        price = get_unit_price("商业综合体", "深圳")
        assert price == 7040.0

    def test_unit_price_bridge_nanjing(self):
        """
        测试南京桥梁单价
        
        南京系数 1.12，基准价 8500 元/m²
        期望：8500 * 1.12 = 9520
        """
        price = get_unit_price("桥梁", "南京")
        assert price == 9520.0

    def test_unit_price_unknown_building_type(self):
        """
        测试未知建筑类型使用默认基准价
        
        基准价 3000 元/m²
        """
        price = get_unit_price("未知类型", "成都")
        assert price == 3000.0 * 1.05  # 成都系数 1.05

    def test_unit_price_unknown_region(self):
        """
        测试未知地区使用默认系数
        
        默认系数 1.0
        """
        price = get_unit_price("住宅楼", "未知地区")
        assert price == 2800.0

    def test_calculate_cost_residential_15k_sqm(self):
        """
        测试15000m²住宅楼成本估算
        
        北京地区：2800 * 1.35 = 3780 元/m²
        总成本：15000 * 3780 / 10000 = 5670 万元
        """
        result = calculate_cost(
            area=15000,
            building_type="住宅楼",
            region="北京",
        )
        
        assert result["total_planned_cost"] == 5670.0
        assert result["cost_per_sqm"] == 3780.0
        assert "breakdown" in result
        assert "土建工程" in result["breakdown"]

    def test_calculate_cost_with_custom_items(self):
        """
        测试带自定义成本明细的成本计算
        
        items 非空时，总成本 = 各明细之和。
        """
        items = [
            {"planned_cost": 3000.0, "actual_cost": 2900.0},
            {"planned_cost": 1500.0, "actual_cost": 1550.0},
        ]
        
        result = calculate_cost(
            area=20000,
            building_type="办公楼",
            region="上海",
            items=items,
        )
        
        assert result["total_planned_cost"] == 4500.0
        assert result["total_actual_cost"] == 4450.0

    def test_calculate_cost_overrun_warning_10_percent(self):
        """
        测试超支10%以上触发预警
        
        实际成本 > 计划成本 * 1.1 时应触发警告。
        """
        items = [
            {"planned_cost": 1000.0, "actual_cost": 1120.0},  # 超支12%
        ]
        
        result = calculate_cost(
            area=5000,
            building_type="住宅楼",
            region="成都",
            items=items,
        )
        
        assert len(result["warning_flags"]) > 0
        warning_text = " ".join(result["warning_flags"])
        assert "10%" in warning_text or "20%" in warning_text

    def test_calculate_cost_overrun_warning_20_percent(self):
        """
        测试超支20%以上触发严重预警
        
        实际成本 > 计划成本 * 1.2 时应触发严重警告。
        """
        items = [
            {"planned_cost": 1000.0, "actual_cost": 1250.0},  # 超支25%
        ]
        
        result = calculate_cost(
            area=5000,
            building_type="住宅楼",
            region="成都",
            items=items,
        )
        
        warning_text = " ".join(result["warning_flags"])
        assert "20%" in warning_text

    def test_calculate_cost_large_project_warning(self):
        """
        测试大型项目（>10万m²）自动预警
        """
        result = calculate_cost(
            area=120000,
            building_type="商业综合体",
            region="深圳",
        )
        
        warning_text = " ".join(result["warning_flags"])
        assert "大型项目" in warning_text

    def test_calculate_cost_zero_area(self):
        """
        测试面积为零时的处理
        
        零面积不应导致除零错误。
        """
        result = calculate_cost(
            area=0,
            building_type="住宅楼",
            region="北京",
        )
        
        assert result["cost_per_sqm"] == 0
        assert result["total_planned_cost"] == 0


# ==================== 成本汇总测试 ====================

class TestCostSummary:
    """
    成本汇总函数测试
    
    验证多项目汇总计算的正确性。
    """

    def test_summarize_costs_normal(self, sample_projects):
        """
        测试正常项目的成本汇总
        
        各项目 status 应正确判断（超支/节省/正常）。
        """
        results = summarize_costs(sample_projects)
        
        assert len(results) == len(sample_projects)
        
        # 验证汇总数据完整性
        for item in results:
            assert "project_name" in item
            assert "variance" in item
            assert "variance_rate" in item
            assert item["status"] in ["超支", "节省", "正常"]

    def test_summarize_costs_overrun_detection(self):
        """
        测试超支项目汇总
        
        上海办公楼：actual=23500 > planned=21000，应判定为超支。
        """
        projects = [
            {"id": 1, "name": "超支项目", "budget": 22000,
             "planned_cost": 21000, "actual_cost": 23500},
        ]
        
        results = summarize_costs(projects)
        assert results[0]["status"] == "超支"
        assert results[0]["variance"] > 0
        assert results[0]["variance_rate"] > 0

    def test_summarize_costs_savings_detection(self):
        """
        测试节省项目汇总
        
        南京桥梁：actual=11000 < planned=11500，应判定为节省。
        """
        projects = [
            {"id": 2, "name": "节省项目", "budget": 12000,
             "planned_cost": 11500, "actual_cost": 11000},
        ]
        
        results = summarize_costs(projects)
        assert results[0]["status"] == "节省"
        assert results[0]["variance"] < 0

    def test_summarize_costs_variance_rate_calculation(self):
        """
        测试偏差率计算公式
        
        偏差率 = (实际 - 计划) / 计划 * 100
        """
        projects = [
            {"id": 1, "name": "测试", "budget": 10000,
             "planned_cost": 10000, "actual_cost": 11000},
        ]
        
        results = summarize_costs(projects)
        # (11000 - 10000) / 10000 * 100 = 10%
        assert results[0]["variance_rate"] == 10.0


# ==================== 超支检测测试 ====================

class TestOverrunDetection:
    """
    超支检测函数测试
    
    验证 detect_overruns 正确识别超支项目。
    """

    def test_detect_overruns_with_overrun_project(self):
        """
        测试超支项目检测
        
        偏差率超过阈值时，项目应被标记为超支。
        """
        projects = [
            {"id": 1, "name": "超支项目", "planned_cost": 10000, "actual_cost": 11000},
        ]
        
        overruns = detect_overruns(projects, threshold=0.05)
        assert len(overruns) == 1
        assert overruns[0]["overrun_rate"] > 5.0

    def test_detect_overruns_no_overrun(self):
        """
        测试无超支时返回空列表
        """
        projects = [
            {"id": 1, "name": "正常项目", "planned_cost": 10000, "actual_cost": 10200},
        ]
        
        overruns = detect_overruns(projects, threshold=0.05)
        assert len(overruns) == 0

    def test_detect_overruns_severity_classification(self):
        """
        测试超支严重程度分级
        
        超支 > 20% 标记为严重，否则为轻微。
        """
        projects = [
            {"id": 1, "name": "轻微超支", "planned_cost": 10000, "actual_cost": 10800},
            {"id": 2, "name": "严重超支", "planned_cost": 10000, "actual_cost": 12500},
        ]
        
        overruns = detect_overruns(projects, threshold=0.05)
        overruns_dict = {o["project_name"]: o for o in overruns}
        
        assert overruns_dict["轻微超支"]["severity"] == "轻微"
        assert overruns_dict["严重超支"]["severity"] == "严重"

    def test_detect_overruns_zero_planned(self):
        """
        测试计划成本为零时跳过检测
        
        零除错误应被正确处理。
        """
        projects = [
            {"id": 1, "name": "零预算项目", "planned_cost": 0, "actual_cost": 0},
        ]
        
        overruns = detect_overruns(projects)
        assert len(overruns) == 0


# ==================== 趋势分析测试 ====================

class TestTrendAnalysis:
    """
    趋势分析函数测试
    
    验证月度数据趋势计算的准确性。
    """

    def test_trend_analysis_increasing(self):
        """
        测试上升趋势识别
        
        最后一个周期实际成本显著高于第一个周期时，趋势为"上升"。
        """
        monthly_data = [
            {"period": "2024-01", "planned": 100, "actual": 95},
            {"period": "2024-02", "planned": 100, "actual": 100},
            {"period": "2024-03", "planned": 100, "actual": 110},
            {"period": "2024-04", "planned": 100, "actual": 120},  # 显著上升
        ]
        
        result = analyze_trend(monthly_data)
        assert result["trend"] == "上升"

    def test_trend_analysis_decreasing(self):
        """
        测试下降趋势识别
        
        最后一个周期实际成本显著低于第一个周期时，趋势为"下降"。
        """
        monthly_data = [
            {"period": "2024-01", "planned": 100, "actual": 120},
            {"period": "2024-02", "planned": 100, "actual": 115},
            {"period": "2024-03", "planned": 100, "actual": 110},
            {"period": "2024-04", "planned": 100, "actual": 105},  # 显著下降
        ]
        
        result = analyze_trend(monthly_data)
        assert result["trend"] == "下降"

    def test_trend_analysis_stable(self):
        """
        测试平稳趋势识别
        
        成本变化在 ±10% 以内时，趋势为"平稳"。
        """
        monthly_data = [
            {"period": "2024-01", "planned": 100, "actual": 100},
            {"period": "2024-02", "planned": 100, "actual": 102},
            {"period": "2024-03", "planned": 100, "actual": 98},
            {"period": "2024-04", "planned": 100, "actual": 101},
        ]
        
        result = analyze_trend(monthly_data)
        assert result["trend"] == "平稳"

    def test_trend_analysis_empty_data(self):
        """
        测试空数据返回无数据结果
        """
        result = analyze_trend([])
        assert result["trend"] == "无数据"

    def test_trend_analysis_insufficient_data(self):
        """
        测试数据不足时的处理
        """
        monthly_data = [
            {"period": "2024-01", "planned": 100, "actual": 100},
        ]
        
        result = analyze_trend(monthly_data)
        assert result["trend"] == "数据不足"

    def test_trend_analysis_cumulative_calculation(self):
        """
        测试累计成本计算
        
        验证每期累计值正确累加。
        """
        monthly_data = [
            {"period": "2024-01", "planned": 100, "actual": 90},
            {"period": "2024-02", "planned": 100, "actual": 110},
            {"period": "2024-03", "planned": 100, "actual": 100},
        ]
        
        result = analyze_trend(monthly_data)
        data_points = result["data_points"]
        
        assert data_points[0]["cumulative_actual"] == 90
        assert data_points[1]["cumulative_actual"] == 200  # 90 + 110
        assert data_points[2]["cumulative_actual"] == 300  # 90 + 110 + 100
        
        assert data_points[0]["cumulative_planned"] == 100
        assert data_points[1]["cumulative_planned"] == 200
        assert data_points[2]["cumulative_planned"] == 300

    def test_trend_analysis_variance_percentage(self):
        """
        测试累计偏差率计算
        
        累计偏差率 = (累计实际 - 累计计划) / 累计计划 * 100
        """
        monthly_data = [
            {"period": "2024-01", "planned": 100, "actual": 90},
            {"period": "2024-02", "planned": 100, "actual": 90},
            {"period": "2024-03", "planned": 100, "actual": 90},
        ]
        
        result = analyze_trend(monthly_data)
        # 累计实际 270，累计计划 300，偏差 -10%
        assert result["variance_percentage"] == -10.0


# ==================== 成本预测测试 ====================

class TestCostPrediction:
    """
    成本预测函数测试
    
    验证 predict_final_cost 的准确性。
    """

    def test_predict_normal_project(self):
        """
        测试正常项目成本预测
        
        进度 50%，当前成本 4000，计划总成本 8000
        预测最终成本 = 4000 / 0.5 = 8000（正好等于计划）
        """
        result = predict_final_cost(
            current_cost=4000.0,
            progress=50.0,
            planned_total=8000.0,
        )
        
        assert result["predicted_final_cost"] == 8000.0
        assert result["at_risk"] is False
        assert result["completion_rate"] == 50.0

    def test_predict_overrun_project(self):
        """
        测试超支项目成本预测
        
        进度 50%，当前成本 5000，计划总成本 8000
        预测最终成本 = 5000 / 0.5 = 10000，超支 25%
        """
        result = predict_final_cost(
            current_cost=5000.0,
            progress=50.0,
            planned_total=8000.0,
        )
        
        assert result["predicted_final_cost"] == 10000.0
        assert result["at_risk"] is True
        assert "超支" in result["risk_factors"][0]

    def test_predict_zero_progress(self):
        """
        测试进度为零时的预测
        
        未开工项目返回计划总成本作为预测值。
        """
        result = predict_final_cost(
            current_cost=0.0,
            progress=0.0,
            planned_total=8000.0,
        )
        
        assert result["predicted_final_cost"] == 8000.0
        assert result["at_risk"] is False

    def test_predict_confidence_interval_early_stage(self):
        """
        测试初期阶段的置信区间（宽区间）
        
        进度 < 30% 时，不确定性 25%，置信区间较宽。
        """
        result = predict_final_cost(
            current_cost=1500.0,
            progress=20.0,
            planned_total=8000.0,
        )
        
        # 预测值 = 1500 / 0.2 = 7500
        assert result["predicted_final_cost"] == 7500.0
        # 置信区间宽度应较大
        interval_width = result["confidence_interval_high"] - result["confidence_interval_low"]
        assert interval_width > result["predicted_final_cost"] * 0.4

    def test_predict_confidence_interval_late_stage(self):
        """
        测试后期阶段的置信区间（窄区间）
        
        进度 > 90% 时，不确定性 3%，置信区间很窄。
        """
        result = predict_final_cost(
            current_cost=7600.0,
            progress=95.0,
            planned_total=8000.0,
        )
        
        # 预测值 = 7600 / 0.95 ≈ 8000
        interval_width = result["confidence_interval_high"] - result["confidence_interval_low"]
        assert interval_width < result["predicted_final_cost"] * 0.1

    def test_predict_late_stage_overrun(self):
        """
        测试后期超支预警
        
        进度 > 80% 且预测超支时，触发"后期超支，调整空间有限"警告。
        """
        result = predict_final_cost(
            current_cost=7200.0,
            progress=85.0,
            planned_total=8000.0,
        )
        
        assert result["at_risk"] is True
        risk_text = " ".join(result["risk_factors"])
        assert "后期" in risk_text or "80%" in risk_text

    def test_predict_high_velocity_risk(self):
        """
        测试成本增速过快风险检测
        
        当前成本增速 > 计划总成本 * 1.05 时，触发风险因子。
        """
        result = predict_final_cost(
            current_cost=4500.0,
            progress=50.0,
            planned_total=8000.0,
        )
        
        # 成本速度 = 4500 / 0.5 = 9000 > 8000 * 1.05 = 8400
        risk_text = " ".join(result["risk_factors"])
        assert "增速" in risk_text


# ==================== 项目评分测试 ====================

class TestProjectScore:
    """
    项目健康度评分测试
    
    验证 calculate_project_score 的评分逻辑。
    """

    def test_score_perfect_project(self):
        """
        测试完美项目的评分
        
        计划 = 实际 = 预算，应得满分 100。
        """
        project = {
            "planned_cost": 10000.0,
            "actual_cost": 10000.0,
            "progress": 50.0,
            "expected_progress": 50.0,
            "total_area": 10000,
        }
        
        score = calculate_project_score(project)
        assert score == 100.0

    def test_score_overrun_penalty(self):
        """
        测试超支扣分
        
        每超 1% 扣 2 分。超支 10% 扣 20 分。
        """
        project = {
            "planned_cost": 10000.0,
            "actual_cost": 11000.0,  # 超支 10%
            "progress": 50.0,
            "expected_progress": 50.0,
            "total_area": 10000,
        }
        
        score = calculate_project_score(project)
        # 100 - 10 * 2 = 80
        assert score == 80.0

    def test_score_large_project_bonus(self):
        """
        测试大型项目加分
        
        面积 > 50000 m² 的项目额外加 2 分（封顶100）。
        """
        project = {
            "planned_cost": 10000.0,
            "actual_cost": 10000.0,
            "progress": 50.0,
            "expected_progress": 50.0,
            "total_area": 60000,  # 大型项目
        }
        
        score = calculate_project_score(project)
        # 100 + 2 = 102，但封顶 100
        assert score == 100.0

    def test_score_progress_delay_penalty(self):
        """
        测试进度延误扣分
        
        实际进度落后于预期进度时扣分。
        """
        project = {
            "planned_cost": 10000.0,
            "actual_cost": 10000.0,
            "progress": 30.0,
            "expected_progress": 50.0,  # 落后 20%
            "total_area": 10000,
        }
        
        score = calculate_project_score(project)
        # 100 - 20 * 0.5 = 90
        assert score == 90.0

    def test_score_minimum_zero(self):
        """
        测试评分最低为零分
        
        严重超支情况下，评分不应为负。
        """
        project = {
            "planned_cost": 10000.0,
            "actual_cost": 30000.0,  # 超支 200%
            "progress": 50.0,
            "expected_progress": 50.0,
            "total_area": 10000,
        }
        
        score = calculate_project_score(project)
        assert score >= 0
