"""Tests for static cockpit generation."""

import json
from pathlib import Path
import tempfile
import unittest

from ai.quality.qualitylib.cockpit import build_cockpit


class CockpitTests(unittest.TestCase):
    """SPEC-001 AC-005 dashboard rendering cases."""

    def test_unverified_dashboard_is_visible_and_static(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()
            (root / "docs").mkdir()

            output = build_cockpit(root)
            html = output.read_text(encoding="utf-8")

            self.assertEqual(output, root / "ai" / "cockpit" / "index.html")
            self.assertIn("未验证", html)
            self.assertIn("python ai/quality/quality.py quick", html)
            self.assertIn("<!doctype html>", html)

    def test_visual_hierarchy_and_responsive_rules_ac_001_ac_002(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()

            output = build_cockpit(root)
            html = output.read_text(encoding="utf-8")

            for marker in (
                'class="topbar"',
                'class="hero"',
                'class="status-spotlight status-unverified"',
                'class="metrics"',
                'class="content-layout"',
                'class="spec-list"',
                'id="gates"',
            ):
                self.assertIn(marker, html)
            self.assertIn("@media (max-width: 760px)", html)
            self.assertIn(
                ".progress-acceptance, .progress-tasks { grid-column: 1 / -1; }",
                html,
            )
            self.assertNotIn("<table", html)

    def test_dashboard_assets_remain_self_contained_ac_004(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()

            output = build_cockpit(root)
            html = output.read_text(encoding="utf-8")

            self.assertNotIn("<script src=", html)
            self.assertNotIn("<link", html)
            self.assertNotIn("@import", html)
            self.assertNotIn("http://", html)
            self.assertNotIn("https://", html)
            self.assertIn("代码资产", html)
            self.assertIn("常用命令", html)

    def test_one_click_core_test_controls_ac_001_ac_004(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()

            output = build_cockpit(root)
            html = output.read_text(encoding="utf-8")

            self.assertIn('id="run-core-tests"', html)
            self.assertIn('id="core-test-status"', html)
            self.assertIn("/api/core-tests/run", html)
            self.assertIn("X-Cockpit-Test-Run", html)
            self.assertIn('window.location.protocol === "file:"', html)
            self.assertIn("textContent", html)
            self.assertNotIn(".innerHTML", html)

    def test_status_icons_are_centered_text_glyphs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()

            output = build_cockpit(root)
            html = output.read_text(encoding="utf-8")

            self.assertIn('content: "✓"', html)
            self.assertIn(".status-orb::after {\n  content: \"✓\"; position: absolute; inset: 0; display: grid;", html)
            self.assertIn('content: "!"', html)
            self.assertIn('content: "?"', html)

    def test_one_click_test_panel_lists_all_covered_apis_ac_001_ac_002(self) -> None:
        expected_apis = {
            "POST /user/gen_token",
            "GET /user/get_user_info",
            "PATCH /user/profile",
            "POST /user/logout",
            "GET /user",
            "POST /user",
            "GET /user/{id}",
            "PUT /user/{id}",
            "PATCH /user/{id}",
            "DELETE /user/{id}",
            "GET /user/advanced-search",
            "GET /user/filter-options",
            "GET /role",
            "POST /role",
            "GET /role/{id}",
            "PUT /role/{id}",
            "PATCH /role/{id}",
            "DELETE /role/{id}",
            "GET /role/{id}/menus",
            "PUT /role/{id}/permissions",
            "GET /role/advanced-search",
            "GET /role/filter-options",
            "GET /menu",
            "POST /menu",
            "GET /menu/{id}",
            "PUT /menu/{id}",
            "PATCH /menu/{id}",
            "DELETE /menu/{id}",
            "GET /menu/get_all_menus",
            "GET /menu/advanced-search",
            "GET /menu/filter-options",
            "GET /department",
            "POST /department",
            "GET /department/{id}",
            "PUT /department/{id}",
            "PATCH /department/{id}",
            "DELETE /department/{id}",
            "GET /department/advanced-search",
            "GET /department/filter-options",
            "GET /healthz/",
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()

            html = build_cockpit(root).read_text(encoding="utf-8")

            self.assertEqual(len(expected_apis), 40)
            self.assertIn('id="core-test-api-scope"', html)
            for api in expected_apis:
                self.assertIn(f'data-api="{api}"', html)
            for group in ("用户", "角色", "菜单", "部门"):
                self.assertIn(f">{group}</h3>", html)
            self.assertIn("apiScope.open = true", html)

    def test_report_content_is_html_escaped_and_summarized(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "ai" / "specs").mkdir(parents=True)
            (root / "business" / "UniDjango").mkdir(parents=True)
            (root / "business" / "frontend").mkdir()
            (root / "ai" / "reports").mkdir()
            report = {
                "schema_version": 1,
                "mode": "quick",
                "status": "failed",
                "duration_seconds": 1.25,
                "gates": [
                    {
                        "name": "docs",
                        "status": "failed",
                        "duration_seconds": 0.5,
                        "detail": "<script>alert('x')</script>",
                    }
                ],
            }
            (root / "ai" / "reports" / "report.json").write_text(
                json.dumps(report),
                encoding="utf-8",
            )

            output = build_cockpit(root)
            html = output.read_text(encoding="utf-8")

            self.assertIn("验证失败", html)
            self.assertNotIn("<script>alert('x')</script>", html)
            self.assertIn("&lt;script&gt;alert", html)


if __name__ == "__main__":
    unittest.main()
