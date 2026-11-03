"""SPEC-006 AC-001/AC-003：部门真实 CRUD、权限、分页和筛选接口。"""
from core_test_support import CoreApiTestCase, api_data, create_test_user
from department.models import SysDep
from rest_framework.test import APIClient


class DepartmentApiTests(CoreApiTestCase):
    def test_anonymous_cannot_list_departments(self):
        response = APIClient().get("/department", secure=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["code"], 401)

    def test_user_without_department_permission_is_forbidden(self):
        viewer = create_test_user(
            "department-viewer",
            permissions=("system:user:list",),
        )
        response = self.get_auth_client(viewer).get("/department", secure=True)

        self.assertEqual(response.status_code, 403)

    def test_list_is_paginated_and_filters_by_name(self):
        for index in range(12):
            SysDep.objects.create(dep_name=f"研发部门-{index:02d}", status=1)
        SysDep.objects.create(dep_name="市场部门", status=1)

        response = self.client.get(
            "/department",
            {"search": "研发", "page": 1, "page_size": 5},
            secure=True,
        )
        data = api_data(response)

        self.assertEqual(data["count"], 12)
        self.assertEqual(data["current_page"], 1)
        self.assertEqual(data["page_size"], 5)
        self.assertEqual(len(data["results"]), 5)
        self.assertTrue(all("研发部门" in row["dep_name"] for row in data["results"]))

    def test_create_department_is_retrievable(self):
        response = self.client.post(
            "/department",
            {"dep_name": "产品部", "remark": "负责产品规划"},
            format="json",
            secure=True,
        )
        created = api_data(response)

        detail = api_data(
            self.client.get(f"/department/{created['id']}", secure=True)
        )
        self.assertEqual(detail["dep_name"], "产品部")
        self.assertEqual(detail["remark"], "负责产品规划")
        self.assertEqual(detail["status"], 1)

    def test_duplicate_department_name_is_rejected(self):
        SysDep.objects.create(dep_name="财务部", status=1)

        response = self.client.post(
            "/department",
            {"dep_name": "财务部", "status": 1},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], 400)
        self.assertEqual(SysDep.objects.filter(dep_name="财务部").count(), 1)

    def test_patch_updates_department_without_replacing_other_fields(self):
        department = SysDep.objects.create(
            dep_name="旧部门名称",
            remark="保留备注",
            status=1,
        )

        response = self.client.patch(
            f"/department/{department.id}",
            {"dep_name": "新部门名称"},
            format="json",
            secure=True,
        )
        updated = api_data(response)
        department.refresh_from_db()

        self.assertEqual(updated["dep_name"], "新部门名称")
        self.assertEqual(department.remark, "保留备注")
        self.assertEqual(department.status, 1)

    def test_put_updates_mutable_department_fields(self):
        department = SysDep.objects.create(
            dep_name="运营部",
            remark="旧备注",
            status=1,
        )

        response = self.client.put(
            f"/department/{department.id}",
            {"dep_name": "运营中心", "remark": "新备注", "status": 0},
            format="json",
            secure=True,
        )
        updated = api_data(response)

        self.assertEqual(updated["dep_name"], "运营中心")
        self.assertEqual(updated["status"], 0)
        self.assertEqual(updated["remark"], "新备注")

    def test_delete_department_makes_detail_unavailable(self):
        department = SysDep.objects.create(dep_name="待删除部门", status=1)

        delete_response = self.client.delete(
            f"/department/{department.id}",
            secure=True,
        )
        detail_response = self.client.get(
            f"/department/{department.id}",
            secure=True,
        )

        self.assertEqual(delete_response.status_code, 200)
        self.assertIsNone(delete_response.json()["data"])
        self.assertEqual(detail_response.status_code, 404)

    def test_advanced_search_and_filter_options_are_available(self):
        SysDep.objects.create(dep_name="启用部门", status=1)
        SysDep.objects.create(dep_name="禁用部门", status=0)

        search_data = api_data(
            self.client.get(
                "/department/advanced-search",
                {"status": 0},
                secure=True,
            )
        )
        options = api_data(
            self.client.get("/department/filter-options", secure=True)
        )

        self.assertEqual(search_data["count"], 1)
        self.assertEqual(search_data["results"][0]["dep_name"], "禁用部门")
        self.assertEqual(
            {item["value"] for item in options["status_options"]},
            {0, 1},
        )
