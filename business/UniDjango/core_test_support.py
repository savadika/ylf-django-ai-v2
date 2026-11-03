"""SPEC-006 AC-003: reusable fixtures for core REST API behavior tests.

This module is imported only by tests. It prepares normal user/role/menu rows
through the ORM, while tests observe application behavior through HTTP APIs.
"""

from unittest import mock

from django.contrib.auth.hashers import make_password
from django.test import TestCase
from rest_framework.test import APIClient

from menu.models import SysMenu, SysRoleMenu
from role.models import SysRole, SysUserRole
from user.jwt_auth import encode_token
from user.models import SysUser


CORE_TEST_PASSWORD = "StrongPass123!"
CORE_PERMISSIONS = (
    "system:user:list",
    "system:user:query",
    "system:user:add",
    "system:user:edit",
    "system:user:delete",
    "system:role:list",
    "system:role:query",
    "system:role:add",
    "system:role:edit",
    "system:role:delete",
    "system:role:permission",
    "system:menu:list",
    "system:menu:query",
    "system:menu:add",
    "system:menu:edit",
    "system:menu:delete",
    "system:department:list",
    "system:department:query",
    "system:department:add",
    "system:department:edit",
    "system:department:delete",
)


def create_test_user(
    username,
    *,
    permissions=(),
    active=True,
    password=CORE_TEST_PASSWORD,
    email=None,
):
    """Create a normal test user with an isolated role and permission menus."""
    user = SysUser.objects.create(
        username=username,
        password=make_password(password),
        email=email or f"{username}@example.com",
        status=1 if active else 0,
    )
    role = SysRole.objects.create(
        name=f"Role {username}",
        code=f"role-{username}",
        remark="test fixture",
    )
    SysUserRole.objects.create(user=user, role=role)

    for order_num, permission in enumerate(dict.fromkeys(permissions), start=1):
        menu = SysMenu.objects.create(
            name=f"Permission {permission}",
            menu_type="F",
            perms=permission,
            order_num=order_num,
        )
        SysRoleMenu.objects.create(role=role, menu=menu)
    return user


def authenticated_api_client(user):
    """Return an HTTPS API client authenticated as ``user``."""
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {encode_token(user)}")
    return client


def api_data(response):
    """Return the successful response payload or fail with a readable message."""
    if response.status_code != 200:
        raise AssertionError(
            f"Expected HTTP 200, got {response.status_code}: "
            f"{getattr(response, 'data', None)}"
        )
    payload = response.json()
    if payload.get("code") != 200 or "data" not in payload:
        raise AssertionError(f"Expected API success envelope, got {payload!r}")
    return payload["data"]


class CoreApiTestCase(TestCase):
    """Base test case for authenticated core API behavior tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._log_patch = mock.patch("log.middleware.submit_log")
        cls._log_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._log_patch.stop()
        super().tearDownClass()

    def setUp(self):
        self.admin_user = create_test_user(
            f"api-admin-{self.__class__.__name__.lower()}",
            permissions=("*:*:*",),
        )
        self.client = authenticated_api_client(self.admin_user)

    @staticmethod
    def get_auth_client(user):
        return authenticated_api_client(user)
