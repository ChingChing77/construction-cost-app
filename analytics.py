# analytics.py
# 成本分析引擎 - 建筑工程造价成本分析核心算法
# Author: 黑莓 🫐

import math
import statistics
from typing import List, Dict, Any, Optional, Tuple, Callable
from dataclasses import dataclass, field

from data_generator import (
    ProjectData, MonthlyTrendData,
    COST_TYPES, PROJECT_TYPES,
    compute_cost_variance, compute_execution_rate, detect_anomaly,
    save_projects_to_csv, save_trends_to_csv,
)


# ============================================================
# 分析结果数据结构
# ============================================================

@dataclass
class CostAlert:
    """成本预警"""
    项目编号: str
    项目名称: str
    成本类型: str
    超支金额: float
    超支比例: float
    预警级别: str  # "正常" | "关注" | "警告" | "严重"


@dataclass
class TrendResult:
    """趋势分析结果"""
    周期: str
    项目类型: str
    总预算: float
    总实际成本: float
    总体执行率: float
    环比变化: float
    同比变化: Optional[float]
    趋势判断: str  # "上升" | "下降" | "稳定"


@dataclass
class DistributionResult:
    """成本分布分析结果"""
    成本类型: str
    总金额: float
    占比: float
    预算总额: float
    执行率: float


@dataclass
class PredictionResult:
    """成本预测结果"""
    未来月份: str
    预测总成本: float
    预测执行率: float
    置信区间_下限: float
    置信区间_上限: float
    模型说明: str


@dataclass
class AnomalyResult:
    """异常值检测结果"""
    项目编号: str
    项目名称: str
    检测指标: str
    实际值: float
    期望值: float
    偏差率: float
    异常类型: str  # "超支异常" | "异常节省" | "数据错误"


# ============================================================
# 成本超支/节省检测
# ============================================================

class CostOverrunDetector:
    """成本超支检测器"""

    # 预警阈值配置
    ALERT_THRESHOLDS = {
        "正常": 5.0,     # 超支 ≤ 5%
        "关注": 10.0,    # 超支 5%~10%
        "警告": 20.0,    # 超支 10%~20%
        "严重": float("inf"),  # 超支 > 20%
    }

    @classmethod
    def get_alert_level(cls, overrun_ratio: float) -> str:
        """根据超支比例获取预警级别"""
        ratio = abs(overrun_ratio)
        if ratio <= cls.ALERT_THRESHOLDS["正常"]:
            return "正常"
        elif ratio <= cls.ALERT_THRESHOLDS["关注"]:
            return "关注"
        elif ratio <= cls.ALERT_THRESHOLDS["警告"]:
            return "警告"
        else:
            return "严重"

    @classmethod
    def detect_overruns(cls, projects: List[ProjectData]) -> List[CostAlert]:
        """
        批量检测成本超支

        Args:
            projects: 项目数据列表

        Returns:
            CostAlert 列表，按超支金额降序排列
        """
        alerts = []
        for p in projects:
            overrun_ratio = p.超支比例
            level = cls.get_alert_level(overrun_ratio)

            # 只报告有问题的项目（关注级别及以上）
            if level != "正常":
                alerts.append(CostAlert(
                    项目编号=p.项目编号,
                    项目名称=p.项目名称,
                    成本类型=p.成本类型,
                    超支金额=p.超支金额,
                    超支比例=overrun_ratio,
                    预警级别=level,
                ))

        # 按超支金额降序
        alerts.sort(key=lambda x: x.超支金额, reverse=True)
        return alerts

    @classmethod
    def get_savings(cls, projects: List[ProjectData]) -> List[CostAlert]:
        """
        检测成本节省项目

        Args:
            projects: 项目数据列表

        Returns:
            节省金额 > 5% 的项目列表
        """
        savings = []
        for p in projects:
            if p.超支金额 < 0 and abs(p.超支比例) > 5.0:
                savings.append(CostAlert(
                    项目编号=p.项目编号,
                    项目名称=p.项目名称,
                    成本类型=p.成本类型,
                    超支金额=abs(p.超支金额),  # 存为正值
                    超支比例=p.超支比例,
                    预警级别="节省",
                ))
        savings.sort(key=lambda x: x.超支金额, reverse=True)
        return savings

    @classmethod
    def summarize_by_project(cls, projects: List[ProjectData]) -> Dict[str, Dict[str, Any]]:
        """
        按项目汇总超支情况

        Args:
            projects: 项目数据列表

        Returns:
            {项目编号: {项目名称, 总预算, 总实际, 超支总额, 超支比例}}
        """
        summary: Dict[str, Dict[str, Any]] = {}
        for p in projects:
            pid = p.项目编号
            if pid not in summary:
                summary[pid] = {
                    "项目名称": p.项目名称,
                    "项目类型": p.项目类型,
                    "城市": p.城市,
                    "总预算": 0.0,
                    "总实际成本": 0.0,
                    "成本明细": [],
                }
            summary[pid]["总预算"] += p.预算金额
            summary[pid]["总实际成本"] += p.实际成本
            summary[pid]["成本明细"].append({
                "成本类型": p.成本类型,
                "预算": p.预算金额,
                "实际": p.实际成本,
                "超支": p.超支金额,
            })

        # 计算汇总超支
        for v in summary.values():
            v["超支总额"] = v["总实际成本"] - v["总预算"]
            v["超支比例"] = (v["超支总额"] / v["总预算"] * 100) if v["总预算"] > 0 else 0

        return summary


# ============================================================
# 趋势分析
# ============================================================

class TrendAnalyzer:
    """趋势分析引擎"""

    @classmethod
    def analyze_monthly_trend(
        cls,
        trends: List[MonthlyTrendData],
        window: int = 3,
    ) -> TrendResult:
        """
        分析月度趋势（滑动窗口平均）

        Args:
            trends: 月度趋势数据
            window: 滑动窗口大小（月）

        Returns:
            TrendResult
        """
        if len(trends) < 2:
            return TrendResult(
                周期="N/A", 项目类型=trends[0].项目类型 if trends else "N/A",
                总预算=0, 总实际成本=0, 总体执行率=0,
                环比变化=0, 同比变化=None, 趋势判断="数据不足",
            )

        # 计算最近 window 个月的数据
        recent = trends[-window:]
        prev = trends[-2 * window:-window] if len(trends) >= 2 * window else trends[:-window]

        total_budget = sum(t.总预算 for t in recent)
        total_actual = sum(t.总实际成本 for t in recent)
        prev_budget = sum(t.总预算 for t in prev) if prev else total_budget
        prev_actual = sum(t.总实际成本 for t in prev) if prev else total_actual

        execution_rate = compute_execution_rate(total_budget, total_actual)
        qoq_change = ((total_actual - prev_actual) / prev_actual * 100) if prev_actual > 0 else 0.0

        # 趋势判断：基于执行率变化
        if qoq_change > 3:
            trend = "上升"  # 成本上升（超支增加）
        elif qoq_change < -3:
            trend = "下降"
        else:
            trend = "稳定"

        return TrendResult(
            周期=f"{trends[0].年月} ~ {trends[-1].年月}",
            项目类型=recent[0].项目类型,
            总预算=round(total_budget, 2),
            总实际成本=round(total_actual, 2),
            总体执行率=round(execution_rate, 2),
            环比变化=round(qoq_change, 2),
            同比变化=None,
            趋势判断=trend,
        )

    @classmethod
    def analyze_quarterly(cls, trends: List[MonthlyTrendData]) -> List[TrendResult]:
        """
        季度趋势分析

        Args:
            trends: 月度趋势数据

        Returns:
            每季度一个 TrendResult
        """
        # 按季度分组
        quarters: Dict[str, List[MonthlyTrendData]] = {}
        for t in trends:
            year, month = t.年月.split("-")
            quarter = f"{year}-Q{(int(month) - 1) // 3 + 1}"
            quarters.setdefault(quarter, []).append(t)

        results = []
        sorted_quarters = sorted(quarters.keys())
        for i, q in enumerate(sorted_quarters):
            ts = quarters[q]
            total_budget = sum(t.总预算 for t in ts)
            total_actual = sum(t.总实际成本 for t in ts)
            execution_rate = compute_execution_rate(total_budget, total_actual)

            # 环比
            qoq = 0.0
            if i > 0:
                prev_q = sorted_quarters[i - 1]
                prev_actual = sum(x.总实际成本 for x in quarters[prev_q])
                qoq = ((total_actual - prev_actual) / prev_actual * 100) if prev_actual > 0 else 0.0

            # 趋势
            if qoq > 3:
                trend = "上升"
            elif qoq < -3:
                trend = "下降"
            else:
                trend = "稳定"

            results.append(TrendResult(
                周期=q,
                项目类型=ts[0].项目类型,
                总预算=round(total_budget, 2),
                总实际成本=round(total_actual, 2),
                总体执行率=round(execution_rate, 2),
                环比变化=round(qoq, 2),
                同比变化=None,
                趋势判断=trend,
            ))

        return results

    @classmethod
    def analyze_yearly(cls, trends: List[MonthlyTrendData]) -> List[TrendResult]:
        """年度趋势分析"""
        years: Dict[str, List[MonthlyTrendData]] = {}
        for t in trends:
            year = t.年月.split("-")[0]
            years.setdefault(year, []).append(t)

        results = []
        sorted_years = sorted(years.keys())
        for i, year in enumerate(sorted_years):
            ts = years[year]
            total_budget = sum(t.总预算 for t in ts)
            total_actual = sum(t.总实际成本 for t in ts)
            execution_rate = compute_execution_rate(total_budget, total_actual)

            yoy = 0.0
            if i > 0:
                prev_year = sorted_years[i - 1]
                prev_actual = sum(x.总实际成本 for x in years[prev_year])
                yoy = ((total_actual - prev_actual) / prev_actual * 100) if prev_actual > 0 else 0.0

            trend = "上升" if yoy > 3 else ("下降" if yoy < -3 else "稳定")

            results.append(TrendResult(
                周期=year,
                项目类型=ts[0].项目类型,
                总预算=round(total_budget, 2),
                总实际成本=round(total_actual, 2),
                总体执行率=round(execution_rate, 2),
                环比变化=round(yoy, 2),
                同比变化=None,
                趋势判断=trend,
            ))

        return results


# ============================================================
# 成本分布分析（饼图数据）
# ============================================================

class CostDistributionAnalyzer:
    """成本类型分布分析"""

    @classmethod
    def analyze_by_cost_type(
        cls,
        projects: List[ProjectData],
    ) -> List[DistributionResult]:
        """
        按成本类型分析分布（用于饼图）

        Args:
            projects: 项目数据列表

        Returns:
            各成本类型的分布数据
        """
        # 按成本类型汇总
        type_data: Dict[str, Dict[str, float]] = {}
        for p in projects:
            ct = p.成本类型
            if ct not in type_data:
                type_data[ct] = {"预算": 0.0, "实际": 0.0}
            type_data[ct]["预算"] += p.预算金额
            type_data[ct]["实际"] += p.实际成本

        total_budget = sum(v["预算"] for v in type_data.values())
        results = []
        for ct, v in type_data.items():
            ratio = (v["实际"] / total_budget * 100) if total_budget > 0 else 0
            exec_rate = compute_execution_rate(v["预算"], v["实际"])
            results.append(DistributionResult(
                成本类型=ct,
                总金额=round(v["实际"], 2),
                占比=round(ratio, 2),
                预算总额=round(v["预算"], 2),
                执行率=exec_rate,
            ))

        # 按金额降序
        results.sort(key=lambda x: x.总金额, reverse=True)
        return results

    @classmethod
    def analyze_by_project_type(
        cls,
        projects: List[ProjectData],
    ) -> List[DistributionResult]:
        """按项目类型分析分布"""
        type_data: Dict[str, Dict[str, float]] = {}
        for p in projects:
            pt = p.项目类型
            if pt not in type_data:
                type_data[pt] = {"预算": 0.0, "实际": 0.0}
            type_data[pt]["预算"] += p.预算金额
            type_data[pt]["实际"] += p.实际成本

        total_budget = sum(v["预算"] for v in type_data.values())
        results = []
        for pt, v in type_data.items():
            ratio = (v["实际"] / total_budget * 100) if total_budget > 0 else 0
            exec_rate = compute_execution_rate(v["预算"], v["实际"])
            results.append(DistributionResult(
                成本类型=pt,
                总金额=round(v["实际"], 2),
                占比=round(ratio, 2),
                预算总额=round(v["预算"], 2),
                执行率=exec_rate,
            ))

        results.sort(key=lambda x: x.总金额, reverse=True)
        return results

    @classmethod
    def analyze_by_city(
        cls,
        projects: List[ProjectData],
    ) -> List[DistributionResult]:
        """按城市分析分布"""
        type_data: Dict[str, Dict[str, float]] = {}
        for p in projects:
            city = p.城市
            if city not in type_data:
                type_data[city] = {"预算": 0.0, "实际": 0.0}
            type_data[city]["预算"] += p.预算金额
            type_data[city]["实际"] += p.实际成本

        total_budget = sum(v["预算"] for v in type_data.values())
        results = []
        for city, v in type_data.items():
            ratio = (v["实际"] / total_budget * 100) if total_budget > 0 else 0
            exec_rate = compute_execution_rate(v["预算"], v["实际"])
            results.append(DistributionResult(
                成本类型=city,
                总金额=round(v["实际"], 2),
                占比=round(ratio, 2),
                预算总额=round(v["预算"], 2),
                执行率=exec_rate,
            ))

        results.sort(key=lambda x: x.总金额, reverse=True)
        return results

    @classmethod
    def get_pie_chart_data(
        cls,
        projects: List[ProjectData],
        group_by: str = "cost_type",
    ) -> Dict[str, Any]:
        """
        获取饼图数据

        Args:
            projects: 项目数据
            group_by: 分组方式 "cost_type" | "project_type" | "city"

        Returns:
            {labels: [...], values: [...], percentages: [...]}
        """
        if group_by == "cost_type":
            data = cls.analyze_by_cost_type(projects)
        elif group_by == "project_type":
            data = cls.analyze_by_project_type(projects)
        elif group_by == "city":
            data = cls.analyze_by_city(projects)
        else:
            data = cls.analyze_by_cost_type(projects)

        return {
            "labels": [d.成本类型 for d in data],
            "values": [d.总金额 for d in data],
            "percentages": [d.占比 for d in data],
            "execution_rates": [d.执行率 for d in data],
        }


# ============================================================
# 预算执行率计算
# ============================================================

class ExecutionRateAnalyzer:
    """预算执行率分析"""

    @classmethod
    def compute_project_execution_rate(cls, projects: List[ProjectData]) -> Dict[str, float]:
        """
        计算每个项目的执行率

        Returns:
            {项目编号: 执行率%}
        """
        project_totals: Dict[str, Tuple[float, float]] = {}
        for p in projects:
            if p.项目编号 not in project_totals:
                project_totals[p.项目编号] = (0.0, 0.0)
            b, a = project_totals[p.项目编号]
            project_totals[p.项目编号] = (b + p.预算金额, a + p.实际成本)

        return {
            pid: round(compute_execution_rate(b, a), 2)
            for pid, (b, a) in project_totals.items()
        }

    @classmethod
    def compute_overall_execution_rate(cls, projects: List[ProjectData]) -> float:
        """计算整体执行率"""
        total_budget = sum(p.预算金额 for p in projects)
        total_actual = sum(p.实际成本 for p in projects)
        return compute_execution_rate(total_budget, total_actual)

    @classmethod
    def execution_rate_distribution(
        cls,
        projects: List[ProjectData],
        buckets: Optional[List[Tuple[float, float]]] = None,
    ) -> Dict[str, int]:
        """
        执行率区间分布

        Args:
            buckets: 自定义区间，默认 [0,90), [90,100), [100,110), [110,inf)

        Returns:
            {区间名: 数量}
        """
        if buckets is None:
            buckets = [(0, 90), (90, 100), (100, 110), (110, float("inf"))]

        rates = list(cls.compute_project_execution_rate(projects).values())
        distribution = {}

        for low, high in buckets:
            label = f"{low}%~{high if high != float('inf') else '∞'}"
            count = sum(1 for r in rates if low <= r < high)
            distribution[label] = count

        return distribution

    @classmethod
    def rank_projects_by_execution_rate(
        cls,
        projects: List[ProjectData],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """执行率排名（最好=最节省，最差=最超支）"""
        project_totals: Dict[str, Dict[str, Any]] = {}
        for p in projects:
            if p.项目编号 not in project_totals:
                project_totals[p.项目编号] = {
                    "项目名称": p.项目名称,
                    "项目类型": p.项目类型,
                    "总预算": 0.0,
                    "总实际成本": 0.0,
                }
            project_totals[p.项目编号]["总预算"] += p.预算金额
            project_totals[p.项目编号]["总实际成本"] += p.实际成本

        ranked = []
        for pid, v in project_totals.items():
            rate = compute_execution_rate(v["总预算"], v["总实际成本"])
            ranked.append({
                "项目编号": pid,
                "项目名称": v["项目名称"],
                "项目类型": v["项目类型"],
                "总预算": round(v["总预算"], 2),
                "总实际成本": round(v["总实际成本"], 2),
                "执行率": rate,
            })

        ranked.sort(key=lambda x: x["执行率"])
        return ranked[:top_n]


# ============================================================
# 成本预测（简单线性回归）
# ============================================================

class CostPredictor:
    """基于线性回归的成本预测"""

    @classmethod
    def linear_regression(
        cls,
        x_vals: List[float],
        y_vals: List[float],
    ) -> Tuple[float, float]:
        """
        简单线性回归 y = a*x + b

        Args:
            x_vals: 自变量列表
            y_vals: 因变量列表

        Returns:
            (a, b) 回归系数
        """
        n = len(x_vals)
        if n < 2:
            return 0.0, (sum(y_vals) / n) if n > 0 else 0.0

        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(y_vals)

        numerator = sum((x_vals[i] - x_mean) * (y_vals[i] - y_mean) for i in range(n))
        denominator = sum((x_vals[i] - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return 0.0, y_mean

        a = numerator / denominator
        b = y_mean - a * x_mean
        return round(a, 4), round(b, 2)

    @classmethod
    def predict_next_n_months(
        cls,
        trends: List[MonthlyTrendData],
        n_future: int = 3,
        confidence_level: float = 0.95,
    ) -> List[PredictionResult]:
        """
        预测未来 N 个月的成本

        Args:
            trends: 历史月度趋势数据
            n_future: 预测月份数
            confidence_level: 置信水平（用于计算置信区间）

        Returns:
            PredictionResult 列表
        """
        if len(trends) < 3:
            return []

        # 构造时间序列 x（月份序号）
        x_vals = list(range(1, len(trends) + 1))
        y_vals = [t.总实际成本 for t in trends]

        # 线性回归
        a, b = cls.linear_regression(x_vals, y_vals)

        # 计算残差标准差（用于置信区间）
        y_pred = [a * x + b for x in x_vals]
        residuals = [y_vals[i] - y_pred[i] for i in range(len(y_vals))]
        residual_std = statistics.stdev(residuals) if len(residuals) > 1 else 0.0

        # 置信区间宽度（近似）
        z_score = 1.96 if confidence_level == 0.95 else 1.65  # 90%
        n = len(trends)

        results = []
        last_ym = trends[-1].年月
        last_year, last_month = map(int, last_ym.split("-"))

        for i in range(1, n_future + 1):
            future_x = len(trends) + i
            pred_y = a * future_x + b

            # 置信区间随预测步数增大而扩大
            ci_width = z_score * residual_std * math.sqrt(1 + 1/n + (future_x - x_vals[-1])**2 / sum((x - x_vals[0])**2 for x in x_vals))
            ci_width = max(ci_width, residual_std * 1.5)  # 最小宽度

            # 月份递增
            month = last_month + i
            year = last_year
            while month > 12:
                month -= 12
                year += 1

            future_ym = f"{year}-{month:02d}"
            future_budget = pred_y  # 简化：用预测值作为预算参考

            results.append(PredictionResult(
                未来月份=future_ym,
                预测总成本=round(pred_y, 2),
                预测执行率=100.0,  # 简化假设
                置信区间_下限=round(max(0, pred_y - ci_width), 2),
                置信区间_上限=round(pred_y + ci_width, 2),
                模型说明=f"线性回归 y = {a:.4f}*x + {b:.2f}，R²参考",
            ))

        return results


# ============================================================
# 异常值检测
# ============================================================

class AnomalyDetector:
    """异常值检测引擎"""

    @classmethod
    def detect_execution_rate_anomalies(
        cls,
        projects: List[ProjectData],
        std_threshold: float = 2.0,
    ) -> List[AnomalyResult]:
        """
        基于执行率的异常检测

        检测标准：
        - 执行率 > mean + 2*std（异常超支）
        - 执行率 < mean - 2*std（异常节省）
        """
        project_rates = ExecutionRateAnalyzer.compute_project_execution_rate(projects)

        if not project_rates:
            return []

        rates = list(project_rates.values())
        mean_rate = statistics.mean(rates)
        std_rate = statistics.stdev(rates) if len(rates) > 1 else 0.0

        # 构建项目编号→名称映射
        name_map: Dict[str, str] = {}
        for p in projects:
            name_map[p.项目编号] = p.项目名称

        anomalies = []
        for pid, rate in project_rates.items():
            if detect_anomaly(rate, mean_rate, std_rate, threshold=std_threshold):
                if rate > mean_rate:
                    anomaly_type = "超支异常"
                    expected = mean_rate
                else:
                    anomaly_type = "异常节省"
                    expected = mean_rate

                deviation = ((rate - expected) / expected * 100) if expected > 0 else 0

                anomalies.append(AnomalyResult(
                    项目编号=pid,
                    项目名称=name_map.get(pid, pid),
                    检测指标="执行率",
                    实际值=rate,
                    期望值=round(expected, 2),
                    偏差率=round(deviation, 2),
                    异常类型=anomaly_type,
                ))

        anomalies.sort(key=lambda x: abs(x.偏差率), reverse=True)
        return anomalies

    @classmethod
    def detect_cost_per_unit_anomalies(
        cls,
        projects: List[ProjectData],
        std_threshold: float = 2.0,
    ) -> List[AnomalyResult]:
        """单价异常检测"""
        # 按成本类型分组检测
        type_projects: Dict[str, List[ProjectData]] = {}
        for p in projects:
            type_projects.setdefault(p.成本类型, []).append(p)

        all_anomalies = []
        for ct, ps in type_projects.items():
            unit_prices = [p.实际单价 for p in ps]
            if len(unit_prices) < 3:
                continue

            mean_up = statistics.mean(unit_prices)
            std_up = statistics.stdev(unit_prices) if len(unit_prices) > 1 else 0.0

            for p in ps:
                if detect_anomaly(p.实际单价, mean_up, std_up, threshold=std_threshold):
                    deviation = ((p.实际单价 - mean_up) / mean_up * 100) if mean_up > 0 else 0
                    anomaly_type = "单价异常偏高" if p.实际单价 > mean_up else "单价异常偏低"

                    all_anomalies.append(AnomalyResult(
                        项目编号=p.项目编号,
                        项目名称=p.项目名称,
                        检测指标=f"单价({ct})",
                        实际值=p.实际单价,
                        期望值=round(mean_up, 2),
                        偏差率=round(deviation, 2),
                        异常类型=anomaly_type,
                    ))

        all_anomalies.sort(key=lambda x: abs(x.偏差率), reverse=True)
        return all_anomalies

    @classmethod
    def comprehensive_anomaly_check(
        cls,
        projects: List[ProjectData],
    ) -> Dict[str, List[AnomalyResult]]:
        """
        综合异常检测

        Returns:
            {检测类型: [异常列表]}
        """
        return {
            "执行率异常": cls.detect_execution_rate_anomalies(projects),
            "单价异常": cls.detect_cost_per_unit_anomalies(projects),
        }


# ============================================================
# 综合分析报告生成
# ============================================================

class ComprehensiveAnalyzer:
    """综合分析入口"""

    def __init__(self, projects: List[ProjectData], trends: Optional[List[MonthlyTrendData]] = None):
        self.projects = projects
        self.trends = trends or []

    def full_report(self) -> Dict[str, Any]:
        """生成完整分析报告"""
        report = {
            "数据概况": {
                "项目记录数": len(self.projects),
                "项目类型数": len(set(p.项目类型 for p in self.projects)),
                "成本类型数": len(set(p.成本类型 for p in self.projects)),
                "总预算": round(sum(p.预算金额 for p in self.projects), 2),
                "总实际成本": round(sum(p.实际成本 for p in self.projects), 2),
                "总体执行率": ExecutionRateAnalyzer.compute_overall_execution_rate(self.projects),
            },
            "超支预警": self._summarize_overruns(),
            "成本分布": self._summarize_distribution(),
            "执行率分布": ExecutionRateAnalyzer.execution_rate_distribution(self.projects),
        }

        if self.trends:
            report["月度趋势分析"] = self._summarize_trends()

        return report

    def _summarize_overruns(self) -> Dict[str, Any]:
        alerts = CostOverrunDetector.detect_overruns(self.projects)
        savings = CostOverrunDetector.get_savings(self.projects)
        return {
            "超支项目数": len(alerts),
            "节省项目数": len(savings),
            "TOP超支": [
                {"项目": a.项目名称, "类型": a.成本类型, "超支": a.超支金额, "比例": a.超支比例, "级别": a.预警级别}
                for a in alerts[:5]
            ],
        }

    def _summarize_distribution(self) -> Dict[str, Any]:
        pie_data = CostDistributionAnalyzer.get_pie_chart_data(self.projects, group_by="cost_type")
        return {
            "成本类型分布": {
                "labels": pie_data["labels"][:5],
                "percentages": pie_data["percentages"][:5],
            }
        }

    def _summarize_trends(self) -> Dict[str, Any]:
        if not self.trends:
            return {}
        ta = TrendAnalyzer()
        monthly = ta.analyze_monthly_trend(self.trends)
        quarterly = ta.analyze_quarterly(self.trends)
        return {
            "最近月度": {
                "周期": monthly.周期,
                "执行率": monthly.总体执行率,
                "趋势": monthly.趋势判断,
                "环比": monthly.环比变化,
            },
            "季度数": len(quarterly),
        }


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    from data_generator import ProjectDataGenerator, TimeSeriesGenerator

    print("=" * 60)
    print("测试分析引擎")
    print("=" * 60)

    # 生成测试数据
    gen = ProjectDataGenerator(seed=42)
    projects = gen.generate_projects(n_projects=20, n_cost_types_per_project=4)

    ts_gen = TimeSeriesGenerator(seed=42)
    trends = ts_gen.generate_monthly_trend("住宅楼", n_months=12)

    # 1. 超支检测
    print("\n【超支检测】")
    alerts = CostOverrunDetector.detect_overruns(projects)
    print(f"  超支项目数: {len(alerts)}")
    for a in alerts[:3]:
        print(f"  [{a.预警级别}] {a.项目名称} | {a.成本类型} | 超支 {a.超支金额:,.0f} ({a.超支比例:+.1f}%)")

    # 2. 执行率分析
    print("\n【执行率分析】")
    overall = ExecutionRateAnalyzer.compute_overall_execution_rate(projects)
    print(f"  总体执行率: {overall:.2f}%")
    dist = ExecutionRateAnalyzer.execution_rate_distribution(projects)
    print(f"  执行率分布: {dist}")

    # 3. 成本分布（饼图数据）
    print("\n【成本类型分布】")
    pie = CostDistributionAnalyzer.get_pie_chart_data(projects, group_by="cost_type")
    for label, val, pct in zip(pie["labels"], pie["values"], pie["percentages"]):
        print(f"  {label}: {val:,.0f} ({pct:.1f}%)")

    # 4. 趋势分析
    print("\n【月度趋势分析】")
    monthly_trend = TrendAnalyzer.analyze_monthly_trend(trends)
    print(f"  周期: {monthly_trend.周期}")
    print(f"  执行率: {monthly_trend.总体执行率}% | 趋势: {monthly_trend.趋势判断} | 环比: {monthly_trend.环比变化:+.2f}%")

    # 5. 成本预测
    print("\n【成本预测（未来3个月）】")
    preds = CostPredictor.predict_next_n_months(trends, n_future=3)
    for p in preds:
        print(f"  {p.未来月份}: {p.预测总成本:,.0f} [置信: {p.置信区间_下限:,.0f} ~ {p.置信区间_上限:,.0f}]")

    # 6. 异常检测
    print("\n【异常值检测】")
    anomalies = AnomalyDetector.detect_execution_rate_anomalies(projects)
    print(f"  执行率异常: {len(anomalies)} 项")
    for a in anomalies[:3]:
        print(f"  [{a.异常类型}] {a.项目名称} | 实际: {a.实际值:.1f}% | 期望: {a.期望值:.1f}% | 偏差: {a.偏差率:+.1f}%")


# ============================================================
# 函数式 API 包装层（兼容测试套件）
# ============================================================

from data_generator import CITY_MULTIPLIER

# 地区单价系数映射
_REGION_COEFFICIENTS = {
    "北京": 1.35, "上海": 1.32, "广州": 1.20, "深圳": 1.28,
    "成都": 1.05, "重庆": 1.02, "武汉": 1.08, "西安": 1.00,
    "杭州": 1.18, "南京": 1.12, "天津": 1.10, "苏州": 1.15,
    "默认": 1.00,
}

# 建筑类型基准单价（元/平方米）
_UNIT_PRICE_BASELINE = {
    "住宅楼": 2800, "办公楼": 4200, "商业综合体": 5500,
    "工业厂房": 2200, "桥梁": 8500, "道路": 1200,
    "地铁站": 9000, "医院": 4800, "学校": 3200,
    "体育馆": 4500, "其他": 3000,
}


def get_region_coefficient(region: str) -> float:
    """获取地区价格系数"""
    return _REGION_COEFFICIENTS.get(region, _REGION_COEFFICIENTS["默认"])


def get_unit_price(building_type: str, region: str) -> float:
    """计算综合单价（元/平方米）"""
    base = _UNIT_PRICE_BASELINE.get(building_type, _UNIT_PRICE_BASELINE["其他"])
    region_factor = get_region_coefficient(region)
    return round(base * region_factor, 2)


def calculate_cost(
    area: float,
    building_type: str,
    region: str,
    items: Optional[List[Dict]] = None,
) -> Dict:
    """计算建筑成本（简化函数式接口）"""
    unit_price = get_unit_price(building_type, region)
    total_planned = round(area * unit_price / 10000, 4)
    total_actual = total_planned
    warning_flags: List[str] = []

    breakdown = {
        "土建工程": round(total_planned * 0.45, 4),
        "安装工程": round(total_planned * 0.20, 4),
        "装饰工程": round(total_planned * 0.20, 4),
        "其他费用": round(total_planned * 0.15, 4),
    }

    if items:
        total_planned = sum(item.get("planned_cost", 0) for item in items)
        total_actual = sum(item.get("actual_cost", 0) for item in items)

    if total_actual > total_planned * 1.1:
        warning_flags.append("⚠️ 实际成本超出计划10%以上")
    if total_actual > total_planned * 1.2:
        warning_flags.append("🚨 成本超支超过20%，需重点关注")
    if area > 100000:
        warning_flags.append("📌 大型项目，建议分阶段成本管控")

    cost_per_sqm = round(total_actual * 10000 / area, 2) if area > 0 else 0

    return {
        "total_planned_cost": total_planned,
        "total_actual_cost": total_actual,
        "cost_per_sqm": cost_per_sqm,
        "breakdown": breakdown,
        "warning_flags": warning_flags,
    }


def summarize_costs(projects: List[Dict]) -> List[Dict]:
    """汇总多个项目的成本"""
    results = []
    for p in projects:
        budget = p.get("budget", 0) or p.get("预算金额", 0)
        planned = p.get("planned_cost", 0) or p.get("计划成本", budget * 0.95)
        actual = p.get("actual_cost", 0) or p.get("实际成本", planned)
        variance = actual - planned
        variance_rate = round((variance / planned * 100), 2) if planned > 0 else 0
        status = "超支" if variance > 0 else ("节省" if variance < 0 else "正常")
        results.append({
            "project_id": p.get("id", 0) or p.get("项目编号", 0),
            "project_name": p.get("name", "未知项目") or p.get("项目名称", "未知项目"),
            "total_budget": budget,
            "total_planned": planned,
            "total_actual": actual,
            "variance": round(variance, 4),
            "variance_rate": variance_rate,
            "status": status,
        })
    return results


def detect_overruns(projects: List[Dict], threshold: float = 0.05) -> List[Dict]:
    """检测超支项目"""
    overruns = []
    for p in projects:
        planned = p.get("planned_cost", 0) or p.get("计划成本", 0)
        actual = p.get("actual_cost", 0) or p.get("实际成本", 0)
        if planned <= 0:
            continue
        variance_rate = (actual - planned) / planned
        if variance_rate > threshold:
            overruns.append({
                "project_id": p.get("id", 0) or p.get("项目编号", 0),
                "project_name": p.get("name", "未知项目") or p.get("项目名称", "未知项目"),
                "planned_cost": planned,
                "actual_cost": actual,
                "overrun_amount": round(actual - planned, 4),
                "overrun_rate": round(variance_rate * 100, 2),
                "severity": "严重" if variance_rate > 0.2 else "轻微",
            })
    return overruns


def analyze_trend(monthly_data: List[Dict]) -> Dict:
    """分析成本变化趋势"""
    if not monthly_data:
        return {"trend": "无数据", "cagr": 0, "data_points": []}
    data_points = []
    cumulative_planned = 0.0
    cumulative_actual = 0.0
    for item in monthly_data:
        cumulative_planned += item.get("planned", 0)
        cumulative_actual += item.get("actual", 0)
        data_points.append({
            "period": item.get("period", ""),
            "planned": round(item.get("planned", 0), 4),
            "actual": round(item.get("actual", 0), 4),
            "cumulative_planned": round(cumulative_planned, 4),
            "cumulative_actual": round(cumulative_actual, 4),
        })
    total_variance = cumulative_actual - cumulative_planned
    variance_pct = round((total_variance / cumulative_planned * 100), 2) if cumulative_planned > 0 else 0
    if len(data_points) >= 2:
        first_actual = data_points[0]["actual"]
        last_actual = data_points[-1]["actual"]
        if last_actual > first_actual * 1.1:
            trend = "上升"
        elif last_actual < first_actual * 0.9:
            trend = "下降"
        else:
            trend = "平稳"
    else:
        trend = "数据不足"
    return {
        "trend": trend,
        "total_variance": round(total_variance, 4),
        "variance_percentage": variance_pct,
        "cumulative_planned": round(cumulative_planned, 4),
        "cumulative_actual": round(cumulative_actual, 4),
        "data_points": data_points,
    }


def predict_final_cost(
    current_cost: float,
    progress: float,
    planned_total: float,
) -> Dict:
    """预测项目最终成本"""
    if progress <= 0:
        return {
            "predicted_final_cost": planned_total,
            "confidence_interval_low": planned_total * 0.9,
            "confidence_interval_high": planned_total * 1.1,
            "completion_rate": 0,
            "at_risk": False,
            "risk_factors": ["项目尚未开工"],
        }
    predicted = current_cost / (progress / 100)
    if progress < 30:
        uncertainty = 0.25
    elif progress < 60:
        uncertainty = 0.15
    elif progress < 90:
        uncertainty = 0.08
    else:
        uncertainty = 0.03
    confidence_low = predicted * (1 - uncertainty)
    confidence_high = predicted * (1 + uncertainty)
    risk_factors: List[str] = []
    at_risk = False
    if predicted > planned_total * 1.1:
        at_risk = True
        risk_factors.append("预测成本将超支10%以上")
    if progress > 0:
        cost_velocity = current_cost / (progress / 100)
        if cost_velocity > planned_total * 1.05:
            risk_factors.append("当前成本增速高于计划")
            at_risk = True
    if progress > 80 and predicted > planned_total:
        risk_factors.append("项目后期超支，调整空间有限")
    return {
        "predicted_final_cost": round(predicted, 4),
        "confidence_interval_low": round(confidence_low, 4),
        "confidence_interval_high": round(confidence_high, 4),
        "completion_rate": round(progress, 2),
        "at_risk": at_risk,
        "risk_factors": risk_factors,
    }


def calculate_project_score(project: Dict) -> float:
    """计算项目健康度评分（0-100）"""
    score = 100.0
    planned = project.get("planned_cost", 0) or project.get("计划成本", 0)
    actual = project.get("actual_cost", 0) or project.get("实际成本", planned)
    progress = project.get("progress", 100) or project.get("完成进度", 100)
    if planned > 0:
        cost_variance = (actual - planned) / planned
        score -= max(0, cost_variance * 200)
    expected_progress = project.get("expected_progress", progress)
    if expected_progress > 0:
        progress_diff = progress - expected_progress
        score -= max(0, abs(progress_diff) * 0.5)
    if project.get("total_area", 0) > 50000:
        score = min(100, score + 2)
    return max(0, min(100, round(score, 2)))
