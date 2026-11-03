"""API contract metadata covered by the cockpit core regression run."""

from __future__ import annotations

from typing import Any


CORE_API_GROUPS = (
    {
        "name": "用户",
        "endpoints": (
            {"method": "POST", "path": "/user/gen_token", "description": "登录并签发 JWT"},
            {"method": "GET", "path": "/user/get_user_info", "description": "获取当前用户和权限"},
            {"method": "PATCH", "path": "/user/profile", "description": "修改当前用户资料"},
            {"method": "POST", "path": "/user/logout", "description": "注销并撤销 JWT"},
            {"method": "GET", "path": "/user", "description": "用户列表与搜索"},
            {"method": "POST", "path": "/user", "description": "创建用户"},
            {"method": "GET", "path": "/user/{id}", "description": "用户详情"},
            {"method": "PUT", "path": "/user/{id}", "description": "完整更新用户"},
            {"method": "PATCH", "path": "/user/{id}", "description": "局部更新用户与角色"},
            {"method": "DELETE", "path": "/user/{id}", "description": "删除用户及角色关联"},
            {"method": "GET", "path": "/user/advanced-search", "description": "用户高级搜索"},
            {"method": "GET", "path": "/user/filter-options", "description": "用户筛选选项"},
        ),
    },
    {
        "name": "角色",
        "endpoints": (
            {"method": "GET", "path": "/role", "description": "角色列表与搜索"},
            {"method": "POST", "path": "/role", "description": "创建角色"},
            {"method": "GET", "path": "/role/{id}", "description": "角色详情"},
            {"method": "PUT", "path": "/role/{id}", "description": "完整更新角色"},
            {"method": "PATCH", "path": "/role/{id}", "description": "局部更新角色"},
            {"method": "DELETE", "path": "/role/{id}", "description": "删除角色及关联"},
            {"method": "GET", "path": "/role/{id}/menus", "description": "角色菜单树与权限"},
            {"method": "PUT", "path": "/role/{id}/permissions", "description": "替换角色权限"},
            {"method": "GET", "path": "/role/advanced-search", "description": "角色高级搜索"},
            {"method": "GET", "path": "/role/filter-options", "description": "角色筛选选项"},
        ),
    },
    {
        "name": "菜单",
        "endpoints": (
            {"method": "GET", "path": "/menu", "description": "菜单列表与搜索"},
            {"method": "POST", "path": "/menu", "description": "创建菜单"},
            {"method": "GET", "path": "/menu/{id}", "description": "菜单详情"},
            {"method": "PUT", "path": "/menu/{id}", "description": "完整更新菜单"},
            {"method": "PATCH", "path": "/menu/{id}", "description": "局部更新菜单"},
            {"method": "DELETE", "path": "/menu/{id}", "description": "删除菜单及子树"},
            {"method": "GET", "path": "/menu/get_all_menus", "description": "完整菜单树"},
            {"method": "GET", "path": "/menu/advanced-search", "description": "菜单高级搜索"},
            {"method": "GET", "path": "/menu/filter-options", "description": "菜单筛选选项"},
        ),
    },
    {
        "name": "部门",
        "endpoints": (
            {"method": "GET", "path": "/department", "description": "部门列表与搜索"},
            {"method": "POST", "path": "/department", "description": "创建部门"},
            {"method": "GET", "path": "/department/{id}", "description": "部门详情"},
            {"method": "PUT", "path": "/department/{id}", "description": "完整更新部门"},
            {"method": "PATCH", "path": "/department/{id}", "description": "局部更新部门"},
            {"method": "DELETE", "path": "/department/{id}", "description": "删除部门"},
            {"method": "GET", "path": "/department/advanced-search", "description": "部门高级搜索"},
            {"method": "GET", "path": "/department/filter-options", "description": "部门筛选选项"},
        ),
    },
    {
        "name": "系统",
        "endpoints": (
            {"method": "GET", "path": "/healthz/", "description": "数据库与缓存健康检查"},
        ),
    },
)


def api_scope_payload() -> tuple[dict[str, Any], ...]:
    """Return a JSON-friendly snapshot of the covered API contracts."""
    return tuple(
        {
            "name": group["name"],
            "endpoints": [dict(endpoint) for endpoint in group["endpoints"]],
        }
        for group in CORE_API_GROUPS
    )


def api_contract_count() -> int:
    """Return the number of covered method/path combinations."""
    return sum(len(group["endpoints"]) for group in CORE_API_GROUPS)
