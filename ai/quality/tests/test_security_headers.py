"""SPEC-011 AC-003: production frontend security headers."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[3]
NGINX = ROOT / "business/frontend/nginx/default.conf"
SECURITY_HEADERS = ROOT / "business/frontend/nginx/security-headers.conf"
DOCKERFILE = ROOT / "business/frontend/Dockerfile"
JEST_CONFIG = ROOT / "business/frontend/jest.config.js"
VUE_CONFIG = ROOT / "business/frontend/vue.config.js"
DIST_INDEX = ROOT / "business/frontend/dist/index.html"


class FrontendSecurityHeaderTests(unittest.TestCase):
    def test_nginx_applies_baseline_security_headers(self) -> None:
        config = (
            NGINX.read_text(encoding="utf-8")
            + SECURITY_HEADERS.read_text(encoding="utf-8")
        )

        for marker in (
            "server_tokens off;",
            "Content-Security-Policy",
            "frame-ancestors 'none'",
            "X-Frame-Options \"DENY\"",
            "X-Content-Type-Options \"nosniff\"",
            "Referrer-Policy \"no-referrer\"",
            "Permissions-Policy",
            "Strict-Transport-Security",
        ):
            self.assertIn(marker, config)

    def test_security_header_include_is_copied_into_image(self) -> None:
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn(
            "COPY nginx/security-headers.conf "
            "/etc/nginx/security-headers.conf",
            dockerfile,
        )

    def test_frontend_coverage_includes_core_application_paths(self) -> None:
        config = JEST_CONFIG.read_text(encoding="utf-8")

        self.assertIn("src/**/*.{js,vue}", config)
        for excluded in (
            "!src/utils/auth.js",
            "!src/utils/request.js",
            "!src/views",
            "!src/store",
            "!src/router",
        ):
            self.assertNotIn(excluded, config)

    def test_production_build_avoids_inline_runtime_scripts_ac_001(self) -> None:
        config = VUE_CONFIG.read_text(encoding="utf-8")
        csp = SECURITY_HEADERS.read_text(encoding="utf-8")

        self.assertNotIn("ScriptExtHtmlWebpackPlugin", config)
        self.assertNotIn("inline: /runtime", config)
        self.assertIn("runtimeChunk('single')", config)
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)

        if DIST_INDEX.is_file():
            html = DIST_INDEX.read_text(encoding="utf-8")
            script_tags = re.findall(r"<script\b[^>]*>", html)
            self.assertTrue(script_tags)
            for tag in script_tags:
                self.assertIn("src=", tag, f"内联脚本仍存在：{tag[:120]}")


if __name__ == "__main__":
    unittest.main()
