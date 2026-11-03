"""Regression checks for the cleaned repository structure."""

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]

BUSINESS_VIEWS = (
    "business/frontend/src/views/dashboard/index.vue",
    "business/frontend/src/views/user/index.vue",
    "business/frontend/src/views/role/index.vue",
    "business/frontend/src/views/menu/index.vue",
    "business/frontend/src/views/department/index.vue",
    "business/frontend/src/views/log/index.vue",
    "business/frontend/src/views/login/index.vue",
    "business/frontend/src/views/404.vue",
)

REMOVED_PATHS = (
    "business/frontend/.travis.yml",
    "business/frontend/README-zh.md",
    "business/frontend/README_GENERATOR.md",
    "business/frontend/mock",
    "business/frontend/src/api/table.js",
    "business/frontend/src/views/debug",
    "business/frontend/src/views/example",
    "business/frontend/src/views/form",
    "business/frontend/src/views/nested",
    "business/frontend/src/views/system",
    "business/frontend/src/views/table",
    "business/frontend/src/views/test-menu.vue",
    "business/frontend/src/views/tree",
)


class ProjectStructureTests(unittest.TestCase):
    """SPEC-002 cleanup, SPEC-003 AI boundary and SPEC-004 business boundary."""

    def test_business_workspace_owns_project_surfaces(self) -> None:
        required = (
            "business/UniDjango",
            "business/frontend",
            "business/docker",
            "business/docs",
            "business/scripts",
            "business/docker-compose.yml",
            "business/docker-compose-dev.yml",
            "business/Makefile",
            "business/.env.example",
        )

        for relative in required:
            self.assertTrue(
                (ROOT / relative).exists(),
                f"business 工作区缺少：{relative}",
            )

    def test_root_has_no_business_directories_or_files(self) -> None:
        removed = (
            "UniDjango",
            "frontend",
            "docker",
            "docs",
            "scripts",
            "docker-compose.yml",
            "docker-compose-dev.yml",
            "Makefile",
            ".env.example",
        )

        for relative in removed:
            self.assertFalse(
                (ROOT / relative).exists(),
                f"根目录仍包含业务资产：{relative}",
            )

    def test_ai_workspace_owns_engineering_surfaces(self) -> None:
        required = (
            "ai/README.md",
            "ai/specs/README.md",
            "ai/quality/quality.py",
            "ai/quality/qualitylib/runner.py",
            "ai/quality/tests/test_project_structure.py",
            "ai/docs/CODING_STANDARDS.md",
            "ai/reports",
            "ai/cockpit/index.html",
        )

        for relative in required:
            self.assertTrue(
                (ROOT / relative).exists(),
                f"AI 工作区缺少：{relative}",
            )

    def test_business_tree_has_no_legacy_ai_paths(self) -> None:
        removed = (
            "specs/README.md",
            "quality/policy.json",
            "scripts/quality.py",
            "scripts/qualitylib",
            "scripts/tests",
            "pyproject.toml",
            ".quality/report.json",
            "docs/CODING_STANDARDS.md",
            "docs/cockpit/index.html",
        )

        for relative in removed:
            path = ROOT / relative
            has_content = (
                path.is_file()
                if path.suffix
                else path.is_dir()
                and any(
                    item.is_file() and "__pycache__" not in item.parts
                    for item in path.rglob("*")
                )
            )
            self.assertFalse(
                has_content,
                f"旧 AI 路径仍包含文件：{relative}",
            )

    def test_root_adapters_point_to_ai_workspace(self) -> None:
        expectations = {
            "AGENTS.md": "ai/quality/quality.py",
            ".pre-commit-config.yaml": "ai/quality/quality.py",
            ".github/workflows/quality.yml": "ai/quality/quality.py",
        }

        for relative, marker in expectations.items():
            content = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn(marker, content)
            self.assertIn("ai/", content)

    def test_initialized_business_views_remain(self) -> None:
        for relative in BUSINESS_VIEWS:
            self.assertTrue(
                (ROOT / relative).is_file(),
                f"业务页面被误删：{relative}",
            )

    def test_initialization_command_targets_existing_views(self) -> None:
        command = (
            ROOT / "business/UniDjango/user/management/commands/init_admin.py"
        ).read_text(encoding="utf-8")
        expected_components = (
            "dashboard/index",
            "user/index",
            "role/index",
            "menu/index",
            "department/index",
            "log/index",
        )

        for component in expected_components:
            self.assertIn(f"'component': '{component}'", command)
            page = ROOT / "business/frontend/src/views" / f"{component}.vue"
            self.assertTrue(page.is_file(), f"菜单组件不存在：{component}")

    def test_dynamic_layout_compatibility_remains(self) -> None:
        permission = (
            ROOT / "business/frontend/src/store/modules/permission.js"
        ).read_text(encoding="utf-8")

        self.assertIn("'system/index': '__LAYOUT__'", permission)

    def test_template_demo_and_mock_files_are_removed(self) -> None:
        for relative in REMOVED_PATHS:
            path = ROOT / relative
            has_files = (
                path.exists()
                if path.suffix
                else path.is_dir() and any(item.is_file() for item in path.rglob("*"))
            )
            self.assertFalse(has_files, f"无引用模板文件仍然存在：{relative}")

    def test_mock_dependency_is_removed_from_manifest_and_lock(self) -> None:
        package = json.loads(
            (ROOT / "business/frontend/package.json").read_text(encoding="utf-8")
        )
        lock = json.loads(
            (ROOT / "business/frontend/package-lock.json").read_text(
                encoding="utf-8"
            )
        )

        self.assertNotIn("mockjs", package.get("devDependencies", {}))
        self.assertNotIn("node_modules/mockjs", lock.get("packages", {}))
        self.assertNotIn(
            "mockjs",
            lock.get("packages", {}).get("", {}).get("devDependencies", {}),
        )

    def test_engineering_and_deployment_entry_points_remain(self) -> None:
        required = (
            "AGENTS.md",
            "ai/docs/PROJECT_STRUCTURE.md",
            "ai/quality/quality.py",
            "ai/cockpit/index.html",
            ".github/workflows/quality.yml",
            ".agents/skills/code-review/SKILL.md",
            ".claude/skills/code-review",
            "business/docker-compose.yml",
            "business/docker-compose-dev.yml",
            "business/frontend/nginx/default.conf",
        )
        for relative in required:
            self.assertTrue(
                (ROOT / relative).exists(),
                f"工程入口被误删：{relative}",
            )

    def test_makefile_defaults_to_all_business_app_tests(self) -> None:
        makefile = (ROOT / "business/Makefile").read_text(encoding="utf-8")

        self.assertIn("TEST         ?= user role menu department log", makefile)
        self.assertIn("$(PY) test $(TEST)", makefile)


if __name__ == "__main__":
    unittest.main()
