"""Tests for the public quality profile definitions."""

from pathlib import Path
import unittest

from ai.quality.quality import REPO_ROOT, create_parser, gates_for_profile, load_policy


class QualityCliTests(unittest.TestCase):
    """SPEC-001 AC-003/AC-004 profile composition cases."""

    def setUp(self) -> None:
        self.policy = load_policy()

    def test_parser_accepts_three_profiles_and_runtime_options(self) -> None:
        parser = create_parser()

        args = parser.parse_args(
            [
                "full",
                "--backend-runtime",
                "docker",
                "--frontend-runtime",
                "local",
                "--skip",
                "frontend-build",
            ]
        )

        self.assertEqual(args.command, "full")
        self.assertEqual(args.backend_runtime, "docker")
        self.assertEqual(args.skip, ["frontend-build"])

    def test_release_contains_full_regression_and_build_gates(self) -> None:
        gates = gates_for_profile("release", REPO_ROOT, self.policy)
        names = [gate.name for gate in gates]

        for required in (
            "backend-tests",
            "frontend-lint",
            "frontend-tests",
            "frontend-build",
            "deploy-check",
        ):
            self.assertIn(required, names)

    def test_policy_thresholds_are_injected_into_backend_gate(self) -> None:
        gates = gates_for_profile("full", REPO_ROOT, self.policy)
        backend = next(gate for gate in gates if gate.name == "backend-tests")
        frontend = next(gate for gate in gates if gate.name == "frontend-tests")

        command_text = " ".join(" ".join(command.argv) for command in backend.commands)
        frontend_command = " ".join(frontend.commands[0].argv)

        self.assertIn(
            str(self.policy["coverage"]["backend_min_percent"]),
            command_text,
        )
        self.assertIn(
            f'"lines":{self.policy["coverage"]["frontend_min_percent"]}',
            frontend_command,
        )

    def test_backend_gate_explicitly_runs_business_app_tests(self) -> None:
        gates = gates_for_profile("full", REPO_ROOT, self.policy)
        backend = next(gate for gate in gates if gate.name == "backend-tests")
        django_test_command = next(
            command
            for command in backend.commands
            if any(argument.endswith("manage.py") for argument in command.argv)
            and "test" in command.argv
        )

        for label in ("user", "role", "menu", "department", "log"):
            self.assertIn(label, django_test_command.argv)

    def test_docker_backend_bypasses_database_wait_entrypoint(self) -> None:
        gates = gates_for_profile(
            "full",
            REPO_ROOT,
            self.policy,
            backend_runtime="docker",
        )
        backend = next(gate for gate in gates if gate.name == "backend-check")
        command = backend.commands[0].argv

        self.assertIn("--no-deps", command)
        self.assertEqual(command[command.index("--entrypoint") + 1], "python")
        self.assertIn("/workspace", command)


if __name__ == "__main__":
    unittest.main()
