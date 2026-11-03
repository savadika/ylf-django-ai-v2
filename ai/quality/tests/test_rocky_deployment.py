"""SPEC-008/SPEC-011: Rocky Linux one-command deployment contract."""

from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "business/scripts/deploy-rocky.sh"
LEGACY_SCRIPTS = (
    "business/scripts/setup-rocky.sh",
    "business/scripts/bootstrap.sh",
    "business/scripts/prod.sh",
    "business/scripts/switch-docker-mirror.sh",
)


class RockyDeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text(encoding="utf-8")

    def test_single_entrypoint_replaces_legacy_deploy_scripts_ac_001(self) -> None:
        self.assertTrue(SCRIPT.is_file())
        for relative in LEGACY_SCRIPTS:
            self.assertFalse((ROOT / relative).exists(), f"旧部署脚本仍存在：{relative}")
        makefile = (ROOT / "business/Makefile").read_text(encoding="utf-8")
        self.assertNotIn("prod-up:", makefile)
        self.assertNotIn("prod-down:", makefile)
        self.assertIn("deploy:\n\tsudo bash scripts/deploy-rocky.sh", makefile)

    def test_installs_docker_and_starts_production_compose_ac_002(self) -> None:
        for marker in (
            "docker-ce",
            "docker-compose-plugin",
            "systemctl enable --now docker",
            "DJANGO_SECRET_KEY",
            "JWT_SECRET_KEY",
            "MYSQL_ROOT_PASSWORD",
            "REDIS_PASSWORD",
            "firewall-cmd --permanent --add-port",
            "compose_prod build",
            "python manage.py migrate --noinput",
            "compose_prod up -d --no-build --remove-orphans",
        ):
            self.assertIn(marker, self.script)

    def test_redeploy_preserves_database_and_admin_credentials_ac_003(self) -> None:
        for marker in (
            "DB_HAS_DATA",
            "REDIS_HAS_DATA",
            "不会自动轮换",
            ".deploy-credentials",
            "检测到已有管理员凭证，跳过管理员初始化",
            "--reset-admin",
        ):
            self.assertIn(marker, self.script)
        self.assertIn("chmod 600 \"$ENV_FILE\"", self.script)
        self.assertIn("chmod 600 \"$CREDENTIAL_FILE\"", self.script)

    def test_admin_overrides_require_explicit_reset_ac_005(self) -> None:
        self.assertIn(
            "管理员参数只能在首次部署或使用 --reset-admin 时指定",
            self.script,
        )
        self.assertIn(
            'if [[ -f "$CREDENTIAL_FILE" && "$RESET_ADMIN" -eq 0 && '
            '"$ADMIN_ARGS_SET" -eq 1 ]]',
            self.script,
        )

    def test_waits_for_service_and_reports_failures_ac_004(self) -> None:
        for marker in (
            "等待前端和后端就绪",
            "curl -fsS",
            "compose_prod logs --tail=120 backend frontend",
            "服务在 240 秒内未就绪",
        ):
            self.assertIn(marker, self.script)

    def test_readiness_uses_dependency_healthcheck_ac_006(self) -> None:
        for marker in (
            'BACKEND_PORT="$(get_env_value "$ENV_FILE" BACKEND_PORT',
            '/healthz/',
            'http://127.0.0.1:${BACKEND_PORT}/healthz/',
        ):
            self.assertIn(marker, self.script)

    def test_docs_use_only_new_deployment_entrypoint_ac_005(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        operation = (ROOT / "business/docs/OPERATION.md").read_text(encoding="utf-8")

        for content in (readme, operation):
            self.assertIn("business/scripts/deploy-rocky.sh", content)
            for legacy in LEGACY_SCRIPTS:
                self.assertNotIn(Path(legacy).name, content)

    def test_shell_syntax_when_bash_is_available(self) -> None:
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("当前环境没有 Bash，Shell 语法需在 Rocky Linux 主机执行")
        completed = subprocess.run(
            [bash, "-n", str(SCRIPT)],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
