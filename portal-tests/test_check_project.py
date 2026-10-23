"""Observable contract and local Docker lifecycle tests."""
import json
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess

from check_project import ProjectError, check_project, run_project


class ProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.manifest = {
            "version": 1, "kind": "workshop", "title": "Example", "description": "Learn by doing",
            "runtime": {"dockerfile": "Dockerfile", "context": ".", "port": 8080, "healthPath": "/health"},
            "requiredEnv": [],
        }
        (self.root / "Dockerfile").write_text("FROM python:3.12-slim\n")
        (self.root / "README.md").write_text("Run the project locally.")
        self.save()

    def save(self) -> None:
        (self.root / "portal-project.json").write_text(json.dumps(self.manifest))

    def test_accepts_valid_project(self) -> None:
        project = check_project(self.root)
        self.assertEqual(project.port, 8080)
        self.assertEqual(project.dockerfile, self.root / "Dockerfile")

    def test_accepts_integral_json_numbers(self) -> None:
        self.manifest["version"] = 1.0
        self.manifest["runtime"]["port"] = 8080.0
        self.save()
        self.assertEqual(check_project(self.root).port, 8080)

    def test_rejects_missing_dockerfile(self) -> None:
        (self.root / "Dockerfile").unlink()
        with self.assertRaises(ProjectError):
            check_project(self.root)

    def test_rejects_context_escape_and_unsafe_health_paths(self) -> None:
        for context, health in [("..", "/health"), (".", "//evil.example/health"), (".", "/health#fragment")]:
            with self.subTest(context=context, health=health):
                self.manifest["runtime"].update(context=context, healthPath=health)
                self.save()
                with self.assertRaises(ProjectError):
                    check_project(self.root)

    def test_rejects_symlink_escape(self) -> None:
        (self.root / "Dockerfile").unlink()
        (self.root / "Dockerfile").symlink_to("/etc/hosts")
        with self.assertRaises(ProjectError):
            check_project(self.root)

    def test_rejects_invalid_types_and_secret_names(self) -> None:
        for field, value in [("version", True), ("requiredEnv", ["KEY=value"]), ("kind", "service")]:
            with self.subTest(field=field):
                original = self.manifest[field]
                self.manifest[field] = value
                self.save()
                with self.assertRaises(ProjectError):
                    check_project(self.root)
                self.manifest[field] = original

    def test_failed_readiness_always_removes_container_and_image(self) -> None:
        project = check_project(self.root)
        with (
            patch("check_project.docker", return_value="127.0.0.1:49152") as docker,
            patch("check_project.wait_ready", side_effect=ProjectError("not ready")),
        ):
            with self.assertRaisesRegex(ProjectError, "not ready"):
                run_project(project, timeout=1)
        commands = [call.args[0] for call in docker.call_args_list]
        self.assertEqual(commands[-2][0:2], ["rm", "-f"])
        self.assertEqual(commands[-1][0:2], ["image", "rm"])

    def test_failed_build_always_attempts_cleanup(self) -> None:
        with patch("check_project.docker", side_effect=[subprocess.TimeoutExpired("docker", 1), "", ""]) as docker:
            with self.assertRaises(subprocess.TimeoutExpired):
                run_project(check_project(self.root), timeout=1)
        self.assertEqual(docker.call_args_list[-2].args[0][:2], ["rm", "-f"])
        self.assertEqual(docker.call_args_list[-1].args[0][:2], ["image", "rm"])

    def test_forwards_env_by_name_without_secret_in_command(self) -> None:
        self.manifest["requiredEnv"] = ["STARTER_TEST_SECRET"]
        self.save()
        with (
            patch.dict("os.environ", {"STARTER_TEST_SECRET": "private-value"}),
            patch("check_project.docker", return_value="127.0.0.1:49152") as docker,
            patch("check_project.wait_ready"),
        ):
            run_project(check_project(self.root))
        commands = [call.args[0] for call in docker.call_args_list]
        self.assertIn("STARTER_TEST_SECRET", commands[1])
        self.assertNotIn("private-value", str(commands))
        self.assertIn("127.0.0.1::8080", commands[1])

    def test_requires_author_instructions(self) -> None:
        (self.root / "README.md").unlink()
        with self.assertRaisesRegex(ProjectError, "README"):
            check_project(self.root)

    def test_matches_remote_contract_limits(self) -> None:
        original = copy.deepcopy(self.manifest)
        invalid = [
            (None, "title", "x" * 121),
            (None, "description", "x" * 1001),
            (None, "title", "name\x7f"),
            (None, "unexpected", "value"),
            (None, "requiredEnv", [f"ENV_{index}" for index in range(51)]),
            (None, "requiredEnv", ["A" * 129]),
            ("runtime", "unexpected", "value"),
            ("runtime", "dockerfile", "./Dockerfile"),
            ("runtime", "context", "folder//child"),
            ("runtime", "context", "x" * 513),
            ("runtime", "healthPath", "/./health"),
            ("runtime", "healthPath", "/" + "x" * 256),
        ]
        for section, key, value in invalid:
            with self.subTest(section=section, key=key):
                self.manifest = copy.deepcopy(original)
                target = self.manifest[section] if section else self.manifest
                target[key] = value
                self.save()
                with self.assertRaises(ProjectError):
                    check_project(self.root)

    def test_rejects_empty_large_or_binary_required_files(self) -> None:
        for content in (b"", b"text\x00", b"x" * (128 * 1024 + 1)):
            with self.subTest(size=len(content)):
                (self.root / "README.md").write_bytes(content)
                with self.assertRaises(ProjectError):
                    check_project(self.root)

    def test_rejects_internal_symlink_too(self) -> None:
        (self.root / "actual.txt").write_text("FROM python:3.12-slim")
        (self.root / "Dockerfile").unlink()
        (self.root / "Dockerfile").symlink_to("actual.txt")
        with self.assertRaises(ProjectError):
            check_project(self.root)

    def test_cleanup_accepts_already_absent_resources(self) -> None:
        from check_project import docker
        result = subprocess.CompletedProcess([], 1, "", "No such container: example")
        with patch("check_project.subprocess.run", return_value=result):
            self.assertEqual(docker(["rm", "-f", "example"], check=False), "")

    def test_cleanup_reports_daemon_failure(self) -> None:
        from check_project import docker
        result = subprocess.CompletedProcess([], 1, "", "Cannot connect: no such file")
        with patch("check_project.subprocess.run", return_value=result):
            with self.assertRaises(subprocess.CalledProcessError):
                docker(["rm", "-f", "example"], check=False)

    def test_missing_environment_fails_before_docker(self) -> None:
        self.manifest["requiredEnv"] = ["STARTER_TEST_SECRET"]
        self.save()
        with patch.dict("os.environ", {}, clear=True), patch("check_project.docker") as docker:
            with self.assertRaises(ProjectError):
                run_project(check_project(self.root))
            docker.assert_not_called()


if __name__ == "__main__":
    unittest.main()
