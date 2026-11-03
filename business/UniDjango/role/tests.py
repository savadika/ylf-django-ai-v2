"""SPEC-006 AC-001/AC-002：角色 CRUD、权限分配和关联清理。"""
from core_test_support import CoreApiTestCase, api_data, create_test_user
from django.test import TestCase

from menu.models import SysMenu, SysRoleMenu
from role.models import SysRole, SysUserRole
from role.views import SysRoleViewSet
from rest_framework.test import APIClient
from user.models import SysUser


class RoleDestroyTests(TestCase):
    def test_perform_destroy_clears_links(self):
        role = SysRole.objects.create(name='r', code='r')
        user = SysUser.objects.create(
            username='u', password='x', email='u@example.com', status=1,
        )
        menu = SysMenu.objects.create(name='m', menu_type='C')
        SysUserRole.objects.create(user=user, role=role)
        SysRoleMenu.objects.create(role=role, menu=menu)

        viewset = SysRoleViewSet()
        viewset.perform_destroy(role)  # 不应抛 ProtectedError

        self.assertFalse(SysRole.objects.filter(id=role.id).exists())
        self.assertFalse(SysUserRole.objects.filter(role_id=role.id).exists())
        self.assertFalse(SysRoleMenu.objects.filter(role_id=role.id).exists())


class RoleApiTests(CoreApiTestCase):
    def test_anonymous_cannot_list_roles(self):
        response = APIClient().get("/role", secure=True)

        self.assertEqual(response.status_code, 401)

    def test_user_without_role_permission_is_forbidden(self):
        viewer = create_test_user(
            "role-viewer",
            permissions=("system:user:list",),
        )

        response = self.get_auth_client(viewer).get("/role", secure=True)

        self.assertEqual(response.status_code, 403)

    def test_list_is_paginated_and_filters_by_code(self):
        for index in range(12):
            SysRole.objects.create(
                name=f"审计角色-{index:02d}",
                code=f"audit-{index:02d}",
            )
        SysRole.objects.create(name="运营角色", code="operator")

        data = api_data(
            self.client.get(
                "/role",
                {"search": "audit", "page": 1, "page_size": 5},
                secure=True,
            )
        )

        self.assertEqual(data["count"], 12)
        self.assertEqual(len(data["results"]), 5)
        self.assertTrue(
            all(row["code"].startswith("audit-") for row in data["results"])
        )

    def test_create_role_is_retrievable(self):
        created = api_data(
            self.client.post(
                "/role",
                {"name": "测试角色", "code": "test-role", "remark": "接口测试"},
                format="json",
                secure=True,
            )
        )
        detail = api_data(
            self.client.get(f"/role/{created['id']}", secure=True)
        )

        self.assertEqual(detail["name"], "测试角色")
        self.assertEqual(detail["code"], "test-role")
        self.assertEqual(detail["remark"], "接口测试")

    def test_duplicate_role_code_is_rejected(self):
        SysRole.objects.create(name="已有角色", code="duplicate-code")

        response = self.client.post(
            "/role",
            {"name": "另一个角色", "code": "duplicate-code"},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(SysRole.objects.filter(code="duplicate-code").count(), 1)

    def test_patch_and_put_update_role_fields(self):
        role = SysRole.objects.create(
            name="旧角色名",
            code="old-code",
            remark="保留备注",
        )

        patched = api_data(
            self.client.patch(
                f"/role/{role.id}",
                {"name": "新角色名"},
                format="json",
                secure=True,
            )
        )
        replaced = api_data(
            self.client.put(
                f"/role/{role.id}",
                {"name": "最终角色名", "code": "final-code", "remark": "新备注"},
                format="json",
                secure=True,
            )
        )

        self.assertEqual(patched["name"], "新角色名")
        self.assertEqual(patched["remark"], "保留备注")
        self.assertEqual(replaced["name"], "最终角色名")
        self.assertEqual(replaced["code"], "final-code")
        self.assertEqual(replaced["remark"], "新备注")

    def test_role_menus_endpoint_returns_tree_and_permissions(self):
        role = SysRole.objects.create(name="菜单角色", code="menu-role")
        parent = SysMenu.objects.create(
            name="系统设置",
            menu_type="M",
            order_num=1,
            perms="system:settings:list",
        )
        child = SysMenu.objects.create(
            name="用户设置",
            parent=parent,
            menu_type="C",
            order_num=1,
            perms="system:user:list",
        )
        SysRoleMenu.objects.create(role=role, menu=parent)
        SysRoleMenu.objects.create(role=role, menu=child)

        data = api_data(
            self.client.get(f"/role/{role.id}/menus", secure=True)
        )

        self.assertEqual(data["menus"][0]["id"], parent.id)
        self.assertEqual(data["menus"][0]["children"][0]["id"], child.id)
        self.assertEqual(
            set(data["permissions"]),
            {"system:settings:list", "system:user:list"},
        )

    def test_update_permissions_replaces_and_deduplicates_menus(self):
        role = SysRole.objects.create(name="授权角色", code="permission-role")
        menu_a = SysMenu.objects.create(
            name="权限A", menu_type="F", perms="system:a:list",
        )
        menu_b = SysMenu.objects.create(
            name="权限B", menu_type="F", perms="system:b:list",
        )
        SysRoleMenu.objects.create(role=role, menu=menu_a)

        api_data(
            self.client.put(
                f"/role/{role.id}/permissions",
                {"permissions": [menu_a.id, menu_b.id, menu_a.id]},
                format="json",
                secure=True,
            )
        )
        first_state = api_data(
            self.client.get(f"/role/{role.id}/menus", secure=True)
        )
        api_data(
            self.client.put(
                f"/role/{role.id}/permissions",
                {"permissions": [menu_b.id]},
                format="json",
                secure=True,
            )
        )
        second_state = api_data(
            self.client.get(f"/role/{role.id}/menus", secure=True)
        )

        self.assertEqual(
            set(first_state["permissions"]),
            {"system:a:list", "system:b:list"},
        )
        self.assertEqual(second_state["permissions"], ["system:b:list"])

    def test_update_permissions_rejects_non_list_payload(self):
        role = SysRole.objects.create(name="坏载荷角色", code="bad-payload")

        response = self.client.put(
            f"/role/{role.id}/permissions",
            {"permissions": "not-a-list"},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "permissions must be a list")

    def test_update_permissions_with_empty_list_clears_access(self):
        role = SysRole.objects.create(name="清空权限角色", code="clear-permissions")
        menu = SysMenu.objects.create(name="待清空权限", menu_type="F")
        SysRoleMenu.objects.create(role=role, menu=menu)

        response = self.client.put(
            f"/role/{role.id}/permissions",
            {"permissions": []},
            format="json",
            secure=True,
        )
        data = api_data(
            self.client.get(f"/role/{role.id}/menus", secure=True)
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["menus"], [])
        self.assertEqual(data["permissions"], [])

    def test_update_permissions_rejects_non_numeric_menu_ids(self):
        role = SysRole.objects.create(name="非法ID角色", code="bad-id")

        response = self.client.put(
            f"/role/{role.id}/permissions",
            {"permissions": ["abc"]},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("菜单 ID", response.json()["message"])

    def test_update_permissions_rejects_missing_menu(self):
        role = SysRole.objects.create(name="缺失菜单角色", code="missing-menu")

        response = self.client.put(
            f"/role/{role.id}/permissions",
            {"permissions": [999999]},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "存在无效的菜单 ID")

    def test_delete_role_via_api_cleans_user_and_menu_links(self):
        role = SysRole.objects.create(name="待删角色", code="delete-role")
        user = SysUser.objects.create(
            username="role-delete-user",
            password="x",
            email="role-delete-user@example.com",
            status=1,
        )
        menu = SysMenu.objects.create(name="待删角色菜单", menu_type="F")
        SysUserRole.objects.create(user=user, role=role)
        SysRoleMenu.objects.create(role=role, menu=menu)

        response = self.client.delete(f"/role/{role.id}", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SysRole.objects.filter(id=role.id).exists())
        self.assertFalse(SysUserRole.objects.filter(role_id=role.id).exists())
        self.assertFalse(SysRoleMenu.objects.filter(role_id=role.id).exists())
        self.assertTrue(SysUser.objects.filter(id=user.id).exists())

    def test_advanced_search_and_filter_options_are_available(self):
        SysRole.objects.create(name="检索角色", code="search-role")

        data = api_data(
            self.client.get(
                "/role/advanced-search",
                {"search": "search-role"},
                secure=True,
            )
        )
        options = api_data(
            self.client.get("/role/filter-options", secure=True)
        )

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["code"], "search-role")
        self.assertTrue(options["ordering_options"])
