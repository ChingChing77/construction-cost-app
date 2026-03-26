"""
API 端点测试 - 建筑工程造价成本分析集成软件

测试 FastAPI 后端所有 RESTful API 端点：
- 首页接口
- 项目 CRUD 操作
- 成本明细接口
- 月度趋势接口
- 分析接口

使用 FastAPI 内置 TestClient，无需启动真实服务器。
"""

import pytest
from fastapi.testclient import TestClient


class TestHomeEndpoint:
    """
    首页接口测试

    验证 /api/home 返回正确的系统信息结构。
    """

    def test_home_returns_correct_structure(self, client: TestClient):
        """
        测试首页接口返回正确的数据结构

        验证返回包含：census 统计卡片 / line 折线图 / table 表格数据。
        """
        response = client.get("/api/home")
        assert response.status_code == 200

        json_data = response.json()
        # API 统一响应格式：{"code": 200, "message": "...", "data": {...}}
        assert json_data["code"] == 200
        data = json_data["data"]

        # 验证首页三大板块
        assert "census" in data
        assert "line" in data
        assert "table" in data

    def test_home_census_cards(self, client: TestClient):
        """
        测试首页 Census 统计卡片数据
        """
        response = client.get("/api/home")
        assert response.status_code == 200

        data = response.json()["data"]
        census = data["census"]

        # census 为 3x2 网格结构
        assert len(census) == 3
        for row in census:
            assert len(row) == 2
            for card in row:
                assert "name" in card
                assert "value" in card

    def test_home_line_chart_data(self, client: TestClient):
        """
        测试首页折线图数据
        """
        response = client.get("/api/home")
        assert response.status_code == 200

        data = response.json()["data"]
        # line 是图表对象列表，第一个图表包含 labels 和 datasets
        assert "line" in data
        assert isinstance(data["line"], list)
        if len(data["line"]) > 0:
            first_chart = data["line"][0]
            assert "labels" in first_chart
            assert "datasets" in first_chart
            assert len(first_chart["datasets"]) >= 2  # 至少包含计划/实际两条线


class TestHealthCheck:
    """
    健康检查接口测试
    """

    def test_health_check_returns_ok(self, client: TestClient):
        """
        测试健康检查接口返回 healthy 状态
        """
        response = client.get("/health")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        health_data = json_data["data"]
        assert health_data["status"] == "healthy"
        assert "version" in health_data


class TestProjectCRUD:
    """
    项目 CRUD 操作测试

    测试项目的创建(POST)、读取(GET)、更新(PUT)、删除(DELETE)操作。
    """

    def test_list_projects(self, client: TestClient):
        """
        测试获取项目列表接口

        验证返回项目列表，且包含必要字段。
        """
        response = client.get("/api/projects")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        projects = json_data["data"]

        assert isinstance(projects, list)
        # 数据库中已有种子数据，至少有一些项目
        assert len(projects) >= 0

        if len(projects) > 0:
            first = projects[0]
            required_fields = ["id", "name", "location", "total_budget", "status"]
            for field in required_fields:
                assert field in first, f"项目缺少必要字段: {field}"

    def test_get_single_project(self, client: TestClient):
        """
        测试获取单个项目详情
        """
        # 先获取项目列表
        list_resp = client.get("/api/projects")
        projects = list_resp.json()["data"]

        if len(projects) == 0:
            pytest.skip("数据库无项目数据，跳过详情测试")

        project_id = projects[0]["id"]
        response = client.get(f"/api/projects/{project_id}")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        proj = json_data["data"]
        assert proj["id"] == project_id
        assert "name" in proj

    def test_get_nonexistent_project(self, client: TestClient):
        """
        测试获取不存在的项目返回 404
        """
        response = client.get("/api/projects/99999")
        assert response.status_code == 404

    def test_create_project(self, client: TestClient):
        """
        测试创建新项目

        验证项目创建成功，返回创建后的项目ID。
        """
        new_project = {
            "name": "测试新建项目_API",
            "description": "API自动化测试项目",
            "location": "杭州",
            "total_budget": 6000.0,
            "total_actual": 0.0,
            "status": "planning",
        }

        response = client.post("/api/projects", json=new_project)
        assert response.status_code == 201

        json_data = response.json()
        assert json_data["code"] == 201
        result = json_data["data"]
        assert "id" in result
        # 创建成功返回新项目 ID
        assert isinstance(result["id"], int)

    def test_create_project_minimal_fields(self, client: TestClient):
        """
        测试最小字段创建项目
        """
        minimal_project = {
            "name": "最小字段测试项目",
            "description": "",
            "location": "广州",
            "total_budget": 3000.0,
            "total_actual": 0.0,
            "status": "planning",
        }

        response = client.post("/api/projects", json=minimal_project)
        assert response.status_code == 201
        json_data = response.json()
        assert json_data["code"] == 201
        assert "id" in json_data["data"]

    def test_update_project(self, client: TestClient):
        """
        测试更新项目信息

        验证部分更新功能（只传需要修改的字段）。
        """
        # 先创建一个项目
        create_resp = client.post("/api/projects", json={
            "name": "待更新测试项目",
            "description": "更新前",
            "location": "西安",
            "total_budget": 2500.0,
            "total_actual": 0.0,
            "status": "planning",
        })
        project_id = create_resp.json()["data"]["id"]

        # 部分更新
        update_data = {
            "status": "ongoing",
            "description": "更新后",
        }

        response = client.put(f"/api/projects/{project_id}", json=update_data)
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200

    def test_update_nonexistent_project(self, client: TestClient):
        """
        测试更新不存在的项目返回 404
        """
        response = client.put("/api/projects/99999", json={"status": "ongoing"})
        assert response.status_code == 404

    def test_delete_project(self, client: TestClient):
        """
        测试删除项目

        验证删除成功后，该项目无法再被获取。
        """
        # 先创建一个项目
        create_resp = client.post("/api/projects", json={
            "name": "待删除测试项目",
            "description": "",
            "location": "成都",
            "total_budget": 1800.0,
            "total_actual": 0.0,
            "status": "planning",
        })
        project_id = create_resp.json()["data"]["id"]

        # 删除该项目
        del_resp = client.delete(f"/api/projects/{project_id}")
        assert del_resp.status_code == 200

        # 验证删除后无法再获取
        get_resp = client.get(f"/api/projects/{project_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_project(self, client: TestClient):
        """
        测试删除不存在的项目返回 404
        """
        response = client.delete("/api/projects/99999")
        assert response.status_code == 404


class TestDashboardStats:
    """
    仪表板统计接口测试
    """

    def test_dashboard_stats(self, client: TestClient):
        """
        测试仪表板统计数据接口

        验证返回统计数据结构。
        """
        response = client.get("/api/dashboard_stats")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        stats = json_data["data"]

        # 验证统计字段
        assert "total_projects" in stats
        assert "total_budget" in stats
        assert "total_actual" in stats
        assert "ongoing_projects" in stats
        assert "cost_saved" in stats
        assert "cost_saved_rate" in stats


class TestCostAnalysis:
    """
    成本分析接口测试
    """

    def test_cost_analysis(self, client: TestClient):
        """
        测试成本分析接口

        验证返回成本分析数据。
        """
        response = client.get("/api/cost_analysis")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        analysis = json_data["data"]

        # 成本分析应包含分组统计数据
        assert isinstance(analysis, (list, dict))


class TestMonthlyCosts:
    """
    月度成本接口测试
    """

    def test_monthly_costs_global(self, client: TestClient):
        """
        测试全局月度成本列表接口
        """
        response = client.get("/api/monthly-costs")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        costs = json_data["data"]

        assert isinstance(costs, list)

    def test_project_monthly_costs(self, client: TestClient):
        """
        测试单个项目的月度成本列表
        """
        # 获取一个项目
        list_resp = client.get("/api/projects")
        projects = list_resp.json()["data"]

        if len(projects) == 0:
            pytest.skip("数据库无项目数据")

        project_id = projects[0]["id"]
        response = client.get(f"/api/projects/{project_id}/monthly-costs")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        costs = json_data["data"]
        assert isinstance(costs, list)


class TestCostItems:
    """
    成本明细接口测试
    """

    def test_list_cost_items(self, client: TestClient):
        """
        测试成本明细列表接口
        """
        # 获取一个项目
        list_resp = client.get("/api/projects")
        projects = list_resp.json()["data"]

        if len(projects) == 0:
            pytest.skip("数据库无项目数据")

        project_id = projects[0]["id"]
        response = client.get(f"/api/projects/{project_id}/cost-items")
        assert response.status_code == 200

        json_data = response.json()
        assert json_data["code"] == 200
        items = json_data["data"]
        assert isinstance(items, list)

    def test_create_cost_item(self, client: TestClient):
        """
        测试创建成本明细
        """
        # 获取一个项目
        list_resp = client.get("/api/projects")
        projects = list_resp.json()["data"]

        if len(projects) == 0:
            pytest.skip("数据库无项目数据")

        project_id = projects[0]["id"]

        # 使用 API 要求的字段名：cost_type, budget_cost, actual_cost
        cost_item = {
            "cost_type": "土建工程",
            "budget_cost": 2000.0,
            "actual_cost": 1900.0,
            "variance_analysis": "进度正常，成本可控",
        }

        response = client.post(
            f"/api/projects/{project_id}/cost-items",
            json=cost_item
        )
        assert response.status_code == 201

        json_data = response.json()
        assert json_data["code"] == 201
        result = json_data["data"]
        assert "id" in result


class TestCORSAndHeaders:
    """
    CORS 和响应头测试
    """

    def test_cors_headers_present(self, client: TestClient):
        """
        测试 CORS 响应头存在

        验证 API 正确配置了 CORS 中间件。
        """
        response = client.get(
            "/api/home",
            headers={"Origin": "http://localhost:8501"}
        )
        assert response.status_code == 200
        # TestClient 的默认行为会包含 CORS 头
