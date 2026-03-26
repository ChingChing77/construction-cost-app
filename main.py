# -*- coding: utf-8 -*-
"""
建筑工程造价成本分析集成软件 - 后端 API
基于 FastAPI + SQLite 实现项目、成本、仪表盘的完整 RESTful 接口
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

from database import (
    init_database,
    init_sample_data,
    get_all_projects,
    get_project_by_id,
    create_project,
    update_project,
    delete_project,
    get_cost_items_by_project,
    add_cost_item,
    update_cost_item,
    delete_cost_item,
    get_monthly_costs_by_project,
    get_all_monthly_costs,
    get_dashboard_stats,
    get_cost_analysis,
    get_home_data,
)

# ====================== Pydantic 请求/响应模型 ======================

class ProjectCreate(BaseModel):
    """创建项目的请求模型"""
    name: str = Field(..., min_length=1, max_length=200, description="项目名称")
    description: str = Field(default="", description="项目描述")
    location: str = Field(default="", description="项目地点")
    total_budget: float = Field(default=0.0, ge=0, description="总预算")
    total_actual: float = Field(default=0.0, ge=0, description="总实际成本")
    status: str = Field(default="planning", description="项目状态: planning/ongoing/completed")


class ProjectUpdate(BaseModel):
    """更新项目的请求模型（所有字段可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    location: Optional[str] = None
    total_budget: Optional[float] = Field(None, ge=0)
    total_actual: Optional[float] = Field(None, ge=0)
    status: Optional[str] = None


class CostItemCreate(BaseModel):
    """创建成本明细的请求模型"""
    cost_type: str = Field(..., min_length=1, description="成本类型")
    budget_cost: float = Field(default=0.0, ge=0, description="预算成本")
    actual_cost: float = Field(default=0.0, ge=0, description="实际成本")
    variance_analysis: str = Field(default="", description="差异分析说明")


class CostItemUpdate(BaseModel):
    """更新成本明细的请求模型"""
    cost_type: Optional[str] = None
    budget_cost: Optional[float] = Field(None, ge=0)
    actual_cost: Optional[float] = Field(None, ge=0)
    variance_analysis: Optional[str] = None


class CensusItem(BaseModel):
    """统计卡片项"""
    name: str
    value: float


class LineDataset(BaseModel):
    """折线图数据集"""
    label: str
    data: List[float]


class LineData(BaseModel):
    """折线图数据结构"""
    title: Dict[str, str]
    labels: List[str]
    description: str
    datasets: List[LineDataset]
    unit: str


class TableHeader(BaseModel):
    """表格列头"""
    text: str
    value: str


class TableDataItem(BaseModel):
    """表格数据行"""
    projectName: str
    costType: str
    budgetCost: str
    actualCost: str
    varianceAnalysis: str


class TableData(BaseModel):
    """表格数据结构"""
    tableHeader: List[TableHeader]
    tableData: List[TableDataItem]
    description: str
    button: str


class HomeData(BaseModel):
    """首页综合数据"""
    census: List[List[CensusItem]]
    line: List[LineData]
    table: List[TableData]


# ====================== FastAPI 应用初始化 ======================

app = FastAPI(
    title="建筑工程造价成本分析 API",
    description="提供项目创建、成本分析、仪表盘统计等 RESTful 接口",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 添加 CORS 中间件，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================== 启动事件 ======================

@app.on_event("startup")
def startup_event():
    """应用启动时初始化数据库和示例数据"""
    init_database()
    init_sample_data()
    print("[启动] 建筑工程造价成本分析 API 已就绪")


# ====================== 通用响应封装 ======================

def success_response(data: Any, message: str = "操作成功") -> JSONResponse:
    """统一成功响应格式"""
    return JSONResponse(
        status_code=200,
        content={"code": 200, "message": message, "data": data}
    )


def created_response(data: Any, message: str = "创建成功") -> JSONResponse:
    """统一创建成功响应格式"""
    return JSONResponse(
        status_code=201,
        content={"code": 201, "message": message, "data": data}
    )


def error_response(status_code: int, message: str) -> JSONResponse:
    """统一错误响应格式"""
    return JSONResponse(
        status_code=status_code,
        content={"code": status_code, "message": message, "data": None}
    )


# ====================== 项目管理 API ======================

@app.get("/api/projects", tags=["项目管理"])
def list_projects():
    """
    GET /api/projects
    获取所有项目列表
    """
    projects = get_all_projects()
    return success_response(projects, f"共获取 {len(projects)} 个项目")


@app.post("/api/projects", tags=["项目管理"], status_code=201)
def create_project_api(project: ProjectCreate):
    """
    POST /api/projects
    创建新项目
    """
    pid = create_project(
        name=project.name,
        description=project.description,
        location=project.location,
        total_budget=project.total_budget,
        total_actual=project.total_actual,
        status=project.status,
    )
    return created_response({"id": pid}, "项目创建成功")


@app.get("/api/projects/{project_id}", tags=["项目管理"])
def get_project(project_id: int):
    """
    GET /api/projects/{id}
    获取单个项目详情
    """
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID={project_id} 不存在")
    return success_response(project)


@app.put("/api/projects/{project_id}", tags=["项目管理"])
def update_project_api(project_id: int, update: ProjectUpdate):
    """
    PUT /api/projects/{id}
    更新项目信息
    """
    existing = get_project_by_id(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"项目 ID={project_id} 不存在")

    updated = update_project(
        project_id=project_id,
        name=update.name,
        description=update.description,
        location=update.location,
        total_budget=update.total_budget,
        total_actual=update.total_actual,
        status=update.status,
    )
    return success_response({"updated": updated}, "项目更新成功" if updated else "无内容更新")


@app.delete("/api/projects/{project_id}", tags=["项目管理"])
def delete_project_api(project_id: int):
    """
    DELETE /api/projects/{id}
    删除项目（级联删除关联的成本明细和月度数据）
    """
    existing = get_project_by_id(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"项目 ID={project_id} 不存在")

    deleted = delete_project(project_id)
    return success_response({"deleted": deleted}, "项目删除成功")


# ====================== 成本明细 API ======================

@app.get("/api/projects/{project_id}/cost-items", tags=["成本明细"])
def list_cost_items(project_id: int):
    """
    GET /api/projects/{id}/cost-items
    获取项目下的成本明细列表
    """
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID={project_id} 不存在")
    items = get_cost_items_by_project(project_id)
    return success_response(items, f"共 {len(items)} 条成本明细")


@app.post("/api/projects/{project_id}/cost-items", tags=["成本明细"], status_code=201)
def create_cost_item(project_id: int, item: CostItemCreate):
    """
    POST /api/projects/{id}/cost-items
    为项目添加成本明细
    """
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID={project_id} 不存在")

    item_id = add_cost_item(
        project_id=project_id,
        cost_type=item.cost_type,
        budget_cost=item.budget_cost,
        actual_cost=item.actual_cost,
        variance_analysis=item.variance_analysis,
    )
    return created_response({"id": item_id}, "成本明细创建成功")


@app.put("/api/cost-items/{item_id}", tags=["成本明细"])
def update_cost_item_api(item_id: int, update: CostItemUpdate):
    """
    PUT /api/cost-items/{item_id}
    更新成本明细
    """
    updated = update_cost_item(
        item_id=item_id,
        cost_type=update.cost_type,
        budget_cost=update.budget_cost,
        actual_cost=update.actual_cost,
        variance_analysis=update.variance_analysis,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"成本明细 ID={item_id} 不存在")
    return success_response({"updated": updated}, "成本明细更新成功")


@app.delete("/api/cost-items/{item_id}", tags=["成本明细"])
def delete_cost_item_api(item_id: int):
    """
    DELETE /api/cost-items/{item_id}
    删除成本明细
    """
    deleted = delete_cost_item(item_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"成本明细 ID={item_id} 不存在")
    return success_response({"deleted": deleted}, "成本明细删除成功")


# ====================== 月度趋势 API ======================

@app.get("/api/projects/{project_id}/monthly-costs", tags=["月度趋势"])
def list_monthly_costs(project_id: int):
    """
    GET /api/projects/{id}/monthly-costs
    获取项目月度成本趋势
    """
    project = get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"项目 ID={project_id} 不存在")
    data = get_monthly_costs_by_project(project_id)
    return success_response(data)


@app.get("/api/monthly-costs", tags=["月度趋势"])
def list_all_monthly_costs():
    """
    GET /api/monthly-costs
    获取所有项目月度成本趋势汇总
    """
    data = get_all_monthly_costs()
    return success_response(data)


# ====================== 分析与统计 API ======================

@app.get("/api/cost_analysis", tags=["数据分析"])
def cost_analysis():
    """
    GET /api/cost_analysis
    获取成本分析数据（各项目成本对比、类型分布、预算执行率）
    """
    data = get_cost_analysis()
    return success_response(data)


@app.get("/api/dashboard_stats", tags=["数据分析"])
def dashboard_stats():
    """
    GET /api/dashboard_stats
    获取仪表盘统计数据（项目总数、在建数、总预算/实际、节约率等）
    """
    data = get_dashboard_stats()
    return success_response(data)


@app.get("/api/home", tags=["数据分析"])
def home_data():
    """
    GET /api/home
    获取首页综合数据（census 统计卡片 / line 折线图 / table 表格）
    """
    data = get_home_data()
    return success_response(data)


# ====================== 健康检查 ======================

@app.get("/health", tags=["系统"])
def health_check():
    """
    GET /health
    服务健康检查
    """
    return success_response({
        "status": "healthy",
        "service": "construction-cost-api",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    })


# ====================== 全局异常处理 ======================

@app.exception_handler(Exception)
def global_exception_handler(request, exc):
    """捕获未处理异常，返回统一错误格式"""
    return error_response(500, f"服务器内部错误: {str(exc)}")


# ====================== 启动命令提示 ======================

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("建筑工程造价成本分析 API")
    print("文档地址: http://localhost:8000/docs")
    print("=" * 50)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
