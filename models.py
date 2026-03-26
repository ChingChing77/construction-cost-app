"""
Pydantic 数据模型 - 建筑工程造价成本分析集成软件
"""

from typing import Optional, List
from datetime import date
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str = Field(..., description="项目名称")
    project_type: str = Field(..., description="项目类型：住宅楼/办公楼/桥梁/道路/厂房")
    location: str = Field(..., description="项目地点")
    total_area: float = Field(..., description="总建筑面积（平方米）")
    budget: float = Field(..., description="预算金额（万元）")


class ProjectCreate(ProjectBase):
    """创建项目请求模型"""
    start_date: Optional[date] = Field(None, description="计划开工日期")
    expected_end_date: Optional[date] = Field(None, description="计划完工日期")


class ProjectUpdate(BaseModel):
    """更新项目请求模型"""
    name: Optional[str] = None
    project_type: Optional[str] = None
    location: Optional[str] = None
    total_area: Optional[float] = None
    budget: Optional[float] = None
    start_date: Optional[date] = None
    expected_end_date: Optional[date] = None
    status: Optional[str] = None


class ProjectCostItem(BaseModel):
    """项目成本科目模型"""
    item_name: str = Field(..., description="费用科目名称")
    category: str = Field(..., description="科目分类：土建/安装/装饰/其他")
    planned_cost: float = Field(..., description="计划成本（万元）")
    actual_cost: float = Field(0.0, description="实际成本（万元）")
    unit_price: float = Field(..., description="综合单价（元/平方米）")
    quantity: float = Field(..., description="工程量")
    progress: float = Field(0.0, ge=0, le=100, description="完成进度（%）")


class ProjectResponse(ProjectBase):
    """项目响应模型"""
    id: int
    start_date: Optional[date] = None
    expected_end_date: Optional[date] = None
    status: str = "规划中"
    actual_total_cost: float = 0.0
    cost_variance: float = 0.0
    cost_variance_rate: float = 0.0

    class Config:
        from_attributes = True


class CalculateCostRequest(BaseModel):
    """成本计算请求模型"""
    project_id: Optional[int] = None
    items: List[ProjectCostItem] = Field(default_factory=list)
    area: float = Field(..., description="建筑面积（平方米）")
    building_type: str = Field(..., description="建筑类型")
    region: str = Field(..., description="地区（影响价格系数）")


class CalculateCostResponse(BaseModel):
    """成本计算响应模型"""
    total_planned_cost: float
    total_actual_cost: float
    cost_per_sqm: float
    breakdown: dict
    warning_flags: List[str] = Field(default_factory=list)


class CostSummary(BaseModel):
    """成本汇总模型"""
    project_id: int
    project_name: str
    total_budget: float
    total_planned: float
    total_actual: float
    variance: float
    variance_rate: float
    status: str  # 正常/超支/节省


class TrendDataPoint(BaseModel):
    """趋势数据点模型"""
    period: str  # e.g. "2024-01"
    planned: float
    actual: float
    cumulative_planned: float
    cumulative_actual: float


class PredictionResult(BaseModel):
    """预测结果模型"""
    predicted_final_cost: float
    confidence_interval_low: float
    confidence_interval_high: float
    completion_rate: float
    at_risk: bool
    risk_factors: List[str] = Field(default_factory=list)
