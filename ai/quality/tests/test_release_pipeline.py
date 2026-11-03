"""SPEC-012: CI/CD release, deployment and rollback contracts."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

from ai.quality.quality import gates_for_profile, load_policy


ROOT = Path(__file__).resolve().parents[3]
WORKFLOW = ROOT / ".github/workflows/quality.yml"
COMPOSE = ROOT / "business/docker-compose.yml"
DEPLOY_SCRIPT = ROOT / "business/scripts/deploy-release.sh"
ROLLBACK_SCRIPT = ROOT / "business/scripts/rollback-release.sh"
MANIFEST_SCRIPT = ROOT / "business/scripts/release_manifest.py"
README = ROOT / "README.md"
OPERATION = ROOT / "business/docs/OPERATION.md"


def _load_manifest_module():
    spec = importlib.util.spec_from_file_location(
        "release_manifest_under_test",
        MANIFEST_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {MANIFEST_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseManifestTests(unittest.TestCase):
    def test_release_manifest_round_trip_ac_002(self) -> None:
        module = _load_manifest_module()
        digest = "a" * 64
        manifest = module.build_manifest(
            release_id="v1.2.3",
            commit_sha="b" * 40,
            backend_image=f"ghcr.io/example/backend@sha256:{digest}",
            frontend_image=f"ghcr.io/example/frontend@sha256:{digest}",
            source_ref="refs/tags/v1.2.3",
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release.json"
            module.write_manifest(path, manifest)
            loaded = module.load_manifest(path)

        self.assertEqual(loaded, manifest)
        self.assertEqual(loaded["schema_version"], 1)
        self.assertEqual(loaded["release_id"], "v1.2.3")
        self.assertEqual(loaded["commit_sha"], "b" * 40)
        self.assertEqual(loaded["backend_digest"], f"sha256:{digest}")
        self.assertEqual(loaded["frontend_digest"], f"sha256:{digest}")

    def test_release_manifest_rejects_unsafe_release_id_ac_002(self) -> None:
        module = _load_manifest_module()
        with self.assertRaises(module.ReleaseManifestError):
            module.build_manifest(
                release_id="../../production",
                commit_sha="b" * 40,
                backend_image=f"ghcr.io/example/backend@sha256:{'a' * 64}",
                frontend_image=f"ghcr.io/example/frontend@sha256:{'c' * 64}",
                source_ref="refs/tags/../../production",
            )

    def test_release_manifest_requires_digest_pinned_images_ac_002(self) -> None:
        module = _load_manifest_module()
        with self.assertRaises(module.ReleaseManifestError):
            module.build_manifest(
                release_id="v1.2.3",
                commit_sha="b" * 40,
                backend_image="ghcr.io/example/backend:v1.2.3",
                frontend_image=f"ghcr.io/example/frontend@sha256:{'c' * 64}",
                source_ref="refs/tags/v1.2.3",
            )


class ReleasePipelineContractTests(unittest.TestCase):
    def test_release_check_fails_warnings_ac_007(self) -> None:
        deploy = next(
            gate
            for gate in gates_for_profile("release", ROOT, load_policy())
            if gate.name == "deploy-check"
        )
        command = deploy.commands[0]
        fail_level = command.argv.index("--fail-level")
        self.assertEqual(command.argv[fail_level + 1], "WARNING")
        self.assertGreaterEqual(len(command.env["DJANGO_SECRET_KEY"]), 50)
        self.assertGreaterEqual(
            len(
                (ROOT / "business/UniDjango/UniDjango/test_settings.py")
                .read_text(encoding="utf-8")
                .split('SECRET_KEY = "', 1)[1]
                .split('"', 1)[0]
            ),
            50,
        )

    def test_workflow_jobs_are_ordered_and_parseable_ac_001(self) -> None:
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        jobs = workflow["jobs"]
        self.assertEqual(jobs["release"]["needs"], "validate")
        self.assertEqual(jobs["publish"]["needs"], "release")
        self.assertEqual(jobs["deploy"]["needs"], "publish")
        self.assertEqual(
            jobs["publish"]["permissions"]["packages"],
            "write",
        )

    def test_tag_pipeline_publishes_after_release_gate_ac_001(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("packages: write", workflow)
        self.assertIn("docker/build-push-action@v6", workflow)
        self.assertIn("docker/setup-buildx-action@v3", workflow)
        self.assertIn("platforms: linux/amd64", workflow)
        self.assertNotIn("linux/arm64", workflow)
        self.assertNotIn("docker/setup-qemu-action", workflow)
        self.assertIn("push: true", workflow)
        self.assertIn("needs: release", workflow)
        self.assertIn(
            "docker compose --env-file business/.env.example "
            "-f business/docker-compose.yml config --quiet",
            workflow,
        )
        self.assertNotIn(":latest", workflow)

    def test_manifest_is_uploaded_and_deploy_consumes_it_ac_002(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("release_manifest.py", workflow)
        self.assertIn("release-manifest", workflow)
        self.assertIn("deployment-bundle", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("actions/download-artifact@v4", workflow)
        self.assertIn("deploy-release.sh", workflow)

    def test_deploy_uses_immutable_images_backup_and_health_ac_003(self) -> None:
        script = DEPLOY_SCRIPT.read_text(encoding="utf-8")
        for marker in (
            "release_manifest.py",
            " validate ",
            "mysqldump",
            "pull backend frontend",
            "python manage.py migrate --noinput",
            "up -d --no-build",
            "/healthz/",
            "current-release",
            "previous-release",
            "rollback-release.sh",
        ):
            self.assertIn(marker, script)
        self.assertNotIn("--build", script)

    def test_rollback_uses_manifest_and_never_builds_ac_004(self) -> None:
        script = ROLLBACK_SCRIPT.read_text(encoding="utf-8")
        for marker in (
            "release_manifest.py",
            " validate ",
            "BACKEND_IMAGE",
            "FRONTEND_IMAGE",
            "up -d --no-build",
            "/healthz/",
            "current-release",
        ):
            self.assertIn(marker, script)
        self.assertNotIn("--build", script)

    def test_auto_deploy_requires_explicit_enable_and_production_env_ac_005(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("vars.ENABLE_AUTO_DEPLOY == 'true'", workflow)
        self.assertIn("name: production", workflow)
        self.assertIn("DEPLOY_SSH_KEY", workflow)
        self.assertIn("DEPLOY_HOST", workflow)
        self.assertIn("GHCR_TOKEN", workflow)

    def test_compose_requires_release_images_ac_003(self) -> None:
        compose = COMPOSE.read_text(encoding="utf-8")
        self.assertIn("image: ${BACKEND_IMAGE:", compose)
        self.assertIn("image: ${FRONTEND_IMAGE:", compose)
        self.assertNotIn("image: ${BACKEND_CONTAINER_NAME}:latest", compose)
        self.assertNotIn("image: ${FRONTEND_CONTAINER_NAME}:latest", compose)
        self.assertIn("condition: service_healthy", compose)

    def test_release_operations_are_documented_ac_006(self) -> None:
        for path in (README, OPERATION):
            content = path.read_text(encoding="utf-8")
            for marker in (
                "deploy-release.sh",
                "rollback-release.sh",
                "release_manifest.py",
                "ENABLE_AUTO_DEPLOY",
            ):
                self.assertIn(marker, content)

    def test_shell_syntax_when_bash_is_available(self) -> None:
        bash = shutil.which("bash")
        if bash is None:
            self.skipTest("Bash is unavailable on this host")
        for script in (DEPLOY_SCRIPT, ROLLBACK_SCRIPT):
            completed = subprocess.run(
                [bash, "-n", str(script)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
