# data_generator.py
# 数据生成器模块 - 为建筑工程造价分析生成模拟数据
# Author: 黑莓 🫐

import random
import csv
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict

# ============================================================
# 常量定义
# ============================================================

# 建筑项目类型
PROJECT_TYPES = [
    "住宅楼", "办公楼", "商场", "桥梁", "道路",
    "隧道", "地下停车场", "园林绿化", "地铁", "学校",
    "医院", "体育馆", "酒店", "厂房", "仓库"
]

# 成本类型
COST_TYPES = [
    "材料费用", "人工费用", "设备费用", "运输费用", "设计费用",
    "消防费用", "施工费用", "管理费用", "安全费用"
]

# 城市列表（影响单价基准）
CITIES = ["北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "西安", "南京", "重庆"]

# 各成本类型的基准单价（元/平方米 or 元/单位）
COST_TYPE_BASE: Dict[str, float] = {
    "材料费用": 2500,
    "人工费用": 800,
    "设备费用": 600,
    "运输费用": 200,
    "设计费用": 150,
    "消防费用": 180,
    "施工费用": 1200,
    "管理费用": 300,
    "安全费用": 120,
}

# 各项目类型的面积基准（平方米）
PROJECT_AREA_BASE: Dict[str, int] = {
    "住宅楼": 15000,
    "办公楼": 22000,
    "商场": 35000,
    "桥梁": 8000,
    "道路": 12000,
    "隧道": 6000,
    "地下停车场": 18000,
    "园林绿化": 25000,
    "地铁": 50000,
    "学校": 12000,
    "医院": 20000,
    "体育馆": 15000,
    "酒店": 18000,
    "厂房": 25000,
    "仓库": 20000,
}

# 各城市单价系数
CITY_MULTIPLIER: Dict[str, float] = {
    "北京": 1.3, "上海": 1.25, "深圳": 1.2, "广州": 1.1, "杭州": 1.05,
    "成都": 0.9, "武汉": 0.85, "西安": 0.8, "南京": 0.95, "重庆": 0.85,
}

# 随机种子（可复现）
random.seed(42)


# ============================================================
# 数据结构
# ============================================================

@dataclass
class ProjectData:
    """单个项目数据"""
    项目编号: str
    项目名称: str
    项目类型: str
    城市: str
    成本类型: str
    预算金额: float
    实际成本: float
    建筑面积: int
    预算单价: float
    实际单价: float
    超支金额: float
    超支比例: float


@dataclass
class MonthlyTrendData:
    """月度趋势数据"""
    年月: str
    项目类型: str
    总预算: float
    总实际成本: float
    执行率: float


# ============================================================
# 随机偏差算法
# ============================================================

def normal_random(mean: float, std: float, clip: Optional[Tuple[float, float]] = None) -> float:
    """
    生成服从正态分布的随机数

    Args:
        mean: 均值
        std: 标准差
        clip: 可选，限制输出范围 (min, max)

    Returns:
        随机数
    """
    value = random.gauss(mean, std)
    if clip:
        value = max(clip[0], min(clip[1], value))
    return round(value, 2)


def uniform_random(min_val: float, max_val: float) -> float:
    """
    生成均匀分布随机数

    Args:
        min_val: 最小值
        max_val: 最大值

    Returns:
        随机数
    """
    return round(random.uniform(min_val, max_val), 2)


def lognormal_random(median: float, sigma: float = 0.3) -> float:
    """
    生成对数正态分布随机数（适合模拟成本偏移）

    Args:
        median: 中位数（目标值）
        sigma: 对数标准差

    Returns:
        随机数
    """
    # 对数正态分布：从 logN(μ, σ) 采样
    mu = math.log(median)
    value = math.exp(random.gauss(mu, sigma))
    return round(value, 2)


def biased_coin(p: float = 0.6) -> bool:
    """
    概率偏置硬币

    Args:
        p: 返回 True 的概率

    Returns:
        True 或 False
    """
    return random.random() < p


# ============================================================
# 差异分析算法
# ============================================================

def compute_cost_variance(budget: float, actual: float) -> Dict[str, Any]:
    """
    计算成本差异分析

    Args:
        budget: 预算金额
        actual: 实际成本

    Returns:
        包含差异金额、差异率、状态（超支/节省/持平）的字典
    """
    diff = actual - budget
    diff_rate = (diff / budget * 100) if budget != 0 else 0.0

    # 判断状态
    if diff > budget * 0.01:  # 超过预算1%判定为超支
        status = "超支"
    elif diff < -budget * 0.01:  # 低于预算1%判定为节省
        status = "节省"
    else:
        status = "持平"

    return {
        "差异金额": round(diff, 2),
        "差异比例": round(diff_rate, 2),
        "状态": status,
        "预算": budget,
        "实际": actual,
    }


def compute_execution_rate(budget: float, actual: float) -> float:
    """
    计算预算执行率

    执行率 = 实际成本 / 预算金额 × 100%
    - 执行率 < 100% 表示节省
    - 执行率 > 100% 表示超支
    - 执行率 = 100% 表示精确执行

    Args:
        budget: 预算金额
        actual: 实际成本

    Returns:
        执行率百分比
    """
    if budget == 0:
        return 0.0
    return round(actual / budget * 100, 2)


def detect_anomaly(value: float, mean: float, std: float, threshold: float = 2.0) -> bool:
    """
    基于标准差检测异常值

    Args:
        value: 待检测值
        mean: 均值
        std: 标准差
        threshold: 阈值（几倍标准差以内算正常，默认2倍）

    Returns:
        True 表示异常
    """
    if std == 0:
        return value != mean
    z_score = abs((value - mean) / std)
    return z_score > threshold


# ============================================================
# 项目数据生成器
# ============================================================

import math


class ProjectDataGenerator:
    """项目数据生成器"""

    def __init__(self, seed: Optional[int] = 42):
        """
        初始化生成器

        Args:
            seed: 随机种子，用于结果复现
        """
        if seed is not None:
            random.seed(seed)
        self._project_counter = 0

    def _generate_project_id(self) -> str:
        """生成项目编号"""
        self._project_counter += 1
        year = datetime.now().year
        return f"PRJ-{year}-{self._project_counter:04d}"

    def _generate_project_name(self, project_type: str, city: str) -> str:
        """生成项目名称"""
        suffixes = ["一期", "二期", "三期", "A区", "B区", "C区", "南区", "北区", "东区", "西区"]
        suffix = random.choice(suffixes)
        return f"{city}{project_type}{suffix}"

    def _estimate_budget(self, project_type: str, city: str, cost_type: str, area: int) -> float:
        """
        估算预算金额

        预算 = 建筑面积 × 成本类型单价系数 × 城市系数
        """
        base_unit = COST_TYPE_BASE.get(cost_type, 500)
        city_mult = CITY_MULTIPLIER.get(city, 1.0)
        # 不同项目类型对各成本类型的敏感度不同
        sensitivity = {
            "住宅楼": {"材料费用": 1.2, "人工费用": 1.0, "施工费用": 1.1},
            "办公楼": {"材料费用": 1.1, "设计费用": 1.3, "管理费用": 1.2},
            "桥梁": {"设备费用": 1.5, "安全费用": 1.4, "施工费用": 1.3},
            "隧道": {"设备费用": 1.6, "安全费用": 1.5, "施工费用": 1.4},
            "道路": {"材料费用": 1.3, "运输费用": 1.2, "施工费用": 1.1},
            "园林绿化": {"材料费用": 1.4, "人工费用": 1.1, "设计费用": 1.2},
            "地铁": {"设备费用": 1.8, "施工费用": 1.5, "安全费用": 1.6},
        }
        sens = sensitivity.get(project_type, {})
        cost_mult = sens.get(cost_type, 1.0)

        budget = area * base_unit * city_mult * cost_mult
        # 加上随机波动 ±15%
        budget *= uniform_random(0.85, 1.15)
        return budget

    def _generate_actual_cost(self, budget: float, cost_type: str) -> float:
        """
        生成实际成本（基于预算加入偏差）

        偏差策略：
        - 超支概率约55%（建筑行业常见）
        - 对数正态分布，使大多数偏差在±20%内
        """
        if biased_coin(0.55):
            # 超支：对数正态分布，中位数在 105% ~ 115%
            median_mult = uniform_random(1.02, 1.18)
        else:
            # 节省：对数正态分布，中位数在 88% ~ 98%
            median_mult = uniform_random(0.88, 0.98)

        actual = lognormal_random(budget * median_mult, sigma=0.12)
        return actual

    def generate_single_project(
        self,
        project_type: Optional[str] = None,
        city: Optional[str] = None,
        cost_type: Optional[str] = None,
    ) -> ProjectData:
        """
        生成单个项目的一条成本记录

        Args:
            project_type: 项目类型，默认随机
            city: 城市，默认随机
            cost_type: 成本类型，默认随机

        Returns:
            ProjectData 对象
        """
        project_type = project_type or random.choice(PROJECT_TYPES)
        city = city or random.choice(CITIES)
        cost_type = cost_type or random.choice(COST_TYPES)
        area = PROJECT_AREA_BASE.get(project_type, 10000) * uniform_random(0.6, 1.5)

        budget = self._estimate_budget(project_type, city, cost_type, area)
        actual = self._generate_actual_cost(budget, cost_type)

        project_name = self._generate_project_name(project_type, city)
        project_id = self._generate_project_id()

        return ProjectData(
            项目编号=project_id,
            项目名称=project_name,
            项目类型=project_type,
            城市=city,
            成本类型=cost_type,
            预算金额=round(budget, 2),
            实际成本=round(actual, 2),
            建筑面积=int(area),
            预算单价=round(budget / area if area > 0 else 0, 2),
            实际单价=round(actual / area if area > 0 else 0, 2),
            超支金额=round(actual - budget, 2),
            超支比例=round((actual - budget) / budget * 100 if budget > 0 else 0, 2),
        )

    def generate_projects(
        self,
        n_projects: int = 50,
        n_cost_types_per_project: int = 3,
    ) -> List[ProjectData]:
        """
        批量生成项目数据

        Args:
            n_projects: 项目数量
            n_cost_types_per_project: 每个项目的成本类型数量

        Returns:
            ProjectData 列表
        """
        projects = []
        for _ in range(n_projects):
            project_type = random.choice(PROJECT_TYPES)
            city = random.choice(CITIES)
            # 每个项目包含多个成本类型
            cost_types = random.sample(COST_TYPES, k=min(n_cost_types_per_project, len(COST_TYPES)))
            for ct in cost_types:
                projects.append(self.generate_single_project(project_type, city, ct))
        return projects


# ============================================================
# 时间序列数据生成器
# ============================================================

class TimeSeriesGenerator:
    """月度造价趋势数据生成器"""

    def __init__(self, seed: Optional[int] = 42):
        if seed is not None:
            random.seed(seed)

    def generate_monthly_trend(
        self,
        project_type: str,
        start_year: int = 2023,
        start_month: int = 1,
        n_months: int = 24,
        base_value: Optional[float] = None,
    ) -> List[MonthlyTrendData]:
        """
        生成指定项目类型的历史月度趋势数据

        Args:
            project_type: 项目类型
            start_year: 起始年
            start_month: 起始月
            n_months: 月份数量
            base_value: 基准值，默认根据项目类型自动确定

        Returns:
            MonthlyTrendData 列表
        """
        base_value = base_value or PROJECT_AREA_BASE.get(project_type, 10000) * 1000

        # 初始化时间
        year, month = start_year, start_month
        trend_data = []

        # 全局趋势系数（模拟通货膨胀、季节性）
        trend_coef = 1.0
        annual_growth = 0.03  # 年增长率约3%

        for i in range(n_months):
            # 月度随机波动
            seasonal_factor = 1.0 + 0.05 * math.sin(2 * math.pi * month / 12)
            random_factor = uniform_random(0.95, 1.08)
            trend_coef *= (1 + annual_growth / 12)

            budget = base_value * trend_coef * seasonal_factor * random_factor
            # 实际成本有轻微超支倾向
            if biased_coin(0.52):
                actual = budget * uniform_random(1.0, 1.12)
            else:
                actual = budget * uniform_random(0.9, 1.0)

            execution_rate = compute_execution_rate(budget, actual)

            ym_str = f"{year}-{month:02d}"
            trend_data.append(MonthlyTrendData(
                年月=ym_str,
                项目类型=project_type,
                总预算=round(budget, 2),
                总实际成本=round(actual, 2),
                执行率=execution_rate,
            ))

            # 月份递增
            month += 1
            if month > 12:
                month = 1
                year += 1

        return trend_data

    def generate_multi_project_trends(
        self,
        n_months: int = 24,
        project_types: Optional[List[str]] = None,
    ) -> List[MonthlyTrendData]:
        """
        生成多项目类型的月度趋势

        Args:
            n_months: 月份数量
            project_types: 项目类型列表，默认全部

        Returns:
            所有项目类型的月度趋势列表
        """
        project_types = project_types or PROJECT_TYPES[:6]  # 默认取前6种
        all_trends = []
        for pt in project_types:
            all_trends.extend(self.generate_monthly_trend(pt, n_months=n_months))
        return all_trends


# ============================================================
# 数据导出工具
# ============================================================

def save_projects_to_csv(projects: List[ProjectData], filepath: str) -> str:
    """
    将项目数据保存为 CSV 文件

    Args:
        projects: 项目数据列表
        filepath: 保存路径

    Returns:
        保存路径
    """
    if not projects:
        return filepath

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    fieldnames = list(asdict(projects[0]).keys())

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in projects:
            writer.writerow(asdict(p))

    return filepath


def save_trends_to_csv(trends: List[MonthlyTrendData], filepath: str) -> str:
    """保存趋势数据为 CSV"""
    if not trends:
        return filepath

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    fieldnames = list(asdict(trends[0]).keys())

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in trends:
            writer.writerow(asdict(t))

    return filepath


# ============================================================
# 测试入口
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("测试数据生成器")
    print("=" * 50)

    # 测试项目数据生成
    gen = ProjectDataGenerator(seed=42)
    projects = gen.generate_projects(n_projects=10, n_cost_types_per_project=3)
    print(f"\n生成了 {len(projects)} 条项目记录")
    for p in projects[:3]:
        print(f"  [{p.项目编号}] {p.项目名称} | 预算: {p.预算金额:,.0f} | 实际: {p.实际成本:,.0f} | {p.超支比例:+.1f}%")

    # 保存到 CSV
    csv_path = save_projects_to_csv(projects, "/home/ubuntu/.openclaw/workspace/construction_cost/sample_projects.csv")
    print(f"\nCSV 已保存: {csv_path}")

    # 测试时间序列生成
    ts_gen = TimeSeriesGenerator(seed=42)
    trends = ts_gen.generate_monthly_trend("住宅楼", n_months=6)
    print(f"\n生成了 {len(trends)} 条月度趋势")
    for t in trends:
        print(f"  {t.年月} | 预算: {t.总预算:,.0f} | 实际: {t.总实际成本:,.0f} | 执行率: {t.执行率:.1f}%")
