"""SPEC-006 AC-001/AC-002：菜单树、层级约束和真实 CRUD API。"""
from core_test_support import CoreApiTestCase, api_data, create_test_user
from django.test import SimpleTestCase, TestCase

from menu.models import SysMenu, SysRoleMenu
from menu.serializers import SysMenuSerializer
from menu.views import SysMenuViewSet
from role.models import SysRole
from rest_framework.test import APIClient
from utils.menu_tree import build_menu_tree


class BuildMenuTreeTests(SimpleTestCase):
    def test_build_tree_and_collect_permissions(self):
        parent = SysMenu(id=1, name='p', parent_id=None, order_num=1, perms='sys:list')
        child = SysMenu(id=2, name='c', parent_id=1, order_num=1, perms='sys:add')
        roots, permissions = build_menu_tree([parent, child])

        self.assertEqual(len(roots), 1)
        self.assertEqual(roots[0]['id'], 1)
        self.assertEqual(len(roots[0]['children']), 1)
        self.assertEqual(roots[0]['children'][0]['id'], 2)
        self.assertIn('sys:list', permissions)
        self.assertIn('sys:add', permissions)

    def test_orphan_node_becomes_root(self):
        node = SysMenu(id=1, name='n', parent_id=99, order_num=1, perms=None)
        roots, _ = build_menu_tree([node])
        self.assertEqual(len(roots), 1)


class MenuDestroyTests(TestCase):
    def test_perform_destroy_clears_subtree_role_menu_links(self):
        role = SysRole.objects.create(name='r', code='r')
        parent = SysMenu.objects.create(name='parent', menu_type='C')
        child = SysMenu.objects.create(name='child', parent=parent, menu_type='F')
        SysRoleMenu.objects.create(role=role, menu=child)

        viewset = SysMenuViewSet()
        viewset.perform_destroy(parent)  # 不应抛 ProtectedError

        self.assertFalse(SysMenu.objects.filter(id__in=[parent.id, child.id]).exists())
        self.assertFalse(SysRoleMenu.objects.filter(menu_id__in=[parent.id, child.id]).exists())


class MenuCycleValidationTests(TestCase):
    def test_serializer_rejects_self_parent(self):
        menu = SysMenu.objects.create(name='self-parent', menu_type='C')

        serializer = SysMenuSerializer(menu, data={'parent_id': menu.id}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent_id', serializer.errors)

    def test_serializer_rejects_descendant_parent(self):
        parent = SysMenu.objects.create(name='cycle-parent', menu_type='C')
        child = SysMenu.objects.create(name='cycle-child', parent=parent, menu_type='C')
        grandchild = SysMenu.objects.create(name='cycle-grandchild', parent=child, menu_type='C')

        serializer = SysMenuSerializer(parent, data={'parent_id': grandchild.id}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn('parent_id', serializer.errors)


class MenuApiTests(CoreApiTestCase):
    def test_anonymous_cannot_list_menus(self):
        response = APIClient().get("/menu", secure=True)

        self.assertEqual(response.status_code, 401)

    def test_user_without_menu_permission_is_forbidden(self):
        viewer = create_test_user(
            "menu-viewer",
            permissions=("system:user:list",),
        )

        response = self.get_auth_client(viewer).get("/menu", secure=True)

        self.assertEqual(response.status_code, 403)

    def test_list_is_paginated_and_filters_by_permission(self):
        for index in range(12):
            SysMenu.objects.create(
                name=f"测试菜单-{index:02d}",
                menu_type="C",
                perms=f"system:test:view:{index:02d}",
                order_num=index,
            )
        SysMenu.objects.create(
            name="其他菜单",
            menu_type="C",
            perms="system:other:view",
        )

        data = api_data(
            self.client.get(
                "/menu",
                {"search": "system:test", "page": 1, "page_size": 5},
                secure=True,
            )
        )

        self.assertEqual(data["count"], 12)
        self.assertEqual(len(data["results"]), 5)
        self.assertTrue(
            all("system:test" in row["perms"] for row in data["results"])
        )

    def test_create_menu_and_child_are_retrievable(self):
        parent = api_data(
            self.client.post(
                "/menu",
                {
                    "name": "测试父菜单",
                    "menu_type": "M",
                    "path": "/test",
                    "order_num": 10,
                    "perms": "system:test:list",
                },
                format="json",
                secure=True,
            )
        )
        child = api_data(
            self.client.post(
                "/menu",
                {
                    "name": "测试子菜单",
                    "parent_id": parent["id"],
                    "menu_type": "C",
                    "path": "/test/child",
                    "component": "test/child",
                    "order_num": 1,
                    "perms": "system:test:query",
                },
                format="json",
                secure=True,
            )
        )

        detail = api_data(
            self.client.get(f"/menu/{child['id']}", secure=True)
        )

        self.assertEqual(detail["parent_id"], parent["id"])
        self.assertEqual(detail["name"], "测试子菜单")
        self.assertEqual(detail["component"], "test/child")

    def test_get_all_menus_returns_ordered_tree(self):
        parent = SysMenu.objects.create(
            name="树形父菜单",
            menu_type="M",
            order_num=20,
            perms="system:tree:list",
        )
        child_b = SysMenu.objects.create(
            name="树形子菜单B",
            parent=parent,
            menu_type="C",
            order_num=2,
            perms="system:tree:b",
        )
        child_a = SysMenu.objects.create(
            name="树形子菜单A",
            parent=parent,
            menu_type="C",
            order_num=1,
            perms="system:tree:a",
        )

        roots = api_data(
            self.client.get("/menu/get_all_menus", secure=True)
        )
        tree = next(row for row in roots if row["id"] == parent.id)

        self.assertEqual(
            [row["id"] for row in tree["children"]],
            [child_a.id, child_b.id],
        )
        self.assertEqual(tree["perms"], "system:tree:list")

    def test_duplicate_top_level_name_is_rejected(self):
        SysMenu.objects.create(name="重复顶级菜单", menu_type="M")

        response = self.client.post(
            "/menu",
            {"name": "重复顶级菜单", "menu_type": "M"},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("同一层级", response.json()["message"])

    def test_duplicate_sibling_name_is_rejected(self):
        parent = SysMenu.objects.create(name="重复父菜单", menu_type="M")
        SysMenu.objects.create(name="重复子菜单", parent=parent, menu_type="C")

        response = self.client.post(
            "/menu",
            {
                "name": "重复子菜单",
                "parent_id": parent.id,
                "menu_type": "C",
            },
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("同一层级", response.json()["message"])

    def test_patch_and_put_update_menu_fields(self):
        menu = SysMenu.objects.create(
            name="待更新菜单",
            menu_type="C",
            order_num=1,
            perms="system:update:list",
            remark="保留备注",
        )

        patched = api_data(
            self.client.patch(
                f"/menu/{menu.id}",
                {"name": "局部更新菜单"},
                format="json",
                secure=True,
            )
        )
        replaced = api_data(
            self.client.put(
                f"/menu/{menu.id}",
                {
                    "name": "完整更新菜单",
                    "menu_type": "F",
                    "order_num": 3,
                    "perms": "system:update:edit",
                    "remark": "新备注",
                },
                format="json",
                secure=True,
            )
        )

        self.assertEqual(patched["name"], "局部更新菜单")
        self.assertEqual(patched["remark"], "保留备注")
        self.assertEqual(replaced["menu_type"], "F")
        self.assertEqual(replaced["perms"], "system:update:edit")
        self.assertEqual(replaced["remark"], "新备注")

    def test_self_parent_update_is_rejected_by_api(self):
        menu = SysMenu.objects.create(name="接口自身父级", menu_type="M")

        response = self.client.patch(
            f"/menu/{menu.id}",
            {"parent_id": menu.id},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("自身", response.json()["message"])

    def test_descendant_parent_update_is_rejected_by_api(self):
        parent = SysMenu.objects.create(name="接口循环父级", menu_type="M")
        child = SysMenu.objects.create(
            name="接口循环子级",
            parent=parent,
            menu_type="M",
        )

        response = self.client.patch(
            f"/menu/{parent.id}",
            {"parent_id": child.id},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("子级", response.json()["message"])

    def test_invalid_parent_id_is_rejected(self):
        response = self.client.post(
            "/menu",
            {"name": "无效父级菜单", "parent_id": 999999},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)

    def test_delete_menu_via_api_cleans_subtree_role_links(self):
        role = SysRole.objects.create(name="菜单清理角色", code="menu-cleanup")
        parent = SysMenu.objects.create(name="待删父菜单", menu_type="M")
        child = SysMenu.objects.create(
            name="待删子菜单",
            parent=parent,
            menu_type="C",
        )
        SysRoleMenu.objects.create(role=role, menu=child)

        response = self.client.delete(f"/menu/{parent.id}", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            SysMenu.objects.filter(id__in=[parent.id, child.id]).exists()
        )
        self.assertFalse(
            SysRoleMenu.objects.filter(
                menu_id__in=[parent.id, child.id]
            ).exists()
        )

    def test_advanced_search_and_filter_options_are_available(self):
        SysMenu.objects.create(
            name="高级检索菜单",
            menu_type="C",
            perms="system:advanced:query",
        )

        data = api_data(
            self.client.get(
                "/menu/advanced-search",
                {"search": "高级检索"},
                secure=True,
            )
        )
        options = api_data(
            self.client.get("/menu/filter-options", secure=True)
        )

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["perms"], "system:advanced:query")
        self.assertTrue(options["ordering_options"])
