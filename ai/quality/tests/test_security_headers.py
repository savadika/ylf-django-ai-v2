"""SPEC-011 AC-003: production frontend security headers."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
NGINX = ROOT / "business/frontend/nginx/default.conf"
SECURITY_HEADERS = ROOT / "business/frontend/nginx/security-headers.conf"
DOCKERFILE = ROOT / "business/frontend/Dockerfile"
JEST_CONFIG = ROOT / "business/frontend/jest.config.js"


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


if __name__ == "__main__":
    unittest.main()
