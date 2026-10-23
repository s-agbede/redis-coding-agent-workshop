"""Compose contract and isolated lifecycle checks."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from check_project import ProjectError, check_project, normalize_compose, run_project


class ComposeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = {"services": {"web": {"build": {"context": str(self.root), "dockerfile": "Dockerfile"}}}}
        (self.root / "README.md").write_text("Local run instructions")
        (self.root / "Dockerfile").write_text("FROM python:3.12-slim")
        (self.root / "compose.portal.yaml").write_text(json.dumps({"services": {"web": {"build": {"context": ".", "dockerfile": "Dockerfile"}}}}))
        self.manifest = {
            "version": 1, "kind": "demo", "title": "Example", "description": "Example demo",
            "runtime": {"type": "compose", "file": "compose.portal.yaml", "service": "web", "port": 8080, "healthPath": "/health"},
            "requiredEnv": [],
        }
        (self.root / "portal-project.json").write_text(json.dumps(self.manifest))

    def test_compose_structure_without_docker(self) -> None:
        with patch("check_project.docker") as docker:
            project = check_project(self.root)
        self.assertEqual(project.runtime_type, "compose")
        self.assertEqual(project.service, "web")
        docker.assert_not_called()

    def test_only_entry_service_gets_loopback_ephemeral_port(self) -> None:
        self.config["services"]["dependency"] = {"image": "redis:7"}
        with patch("check_project.docker", return_value=json.dumps(self.config)):
            path = normalize_compose(check_project(self.root), self.root, "unique-check")
        resolved = json.loads(path.read_text())
        self.assertEqual(resolved["services"]["web"]["ports"][0]["host_ip"], "127.0.0.1")
        self.assertEqual(resolved["services"]["web"]["ports"][0]["published"], "0")
        self.assertNotIn("ports", resolved["services"]["dependency"])
        self.assertEqual(resolved["services"]["web"]["image"], "unique-check-web:check")

    def test_rejects_host_features_before_build(self) -> None:
        for key, value in [("ports", ["8080:8080"]), ("privileged", True), ("network_mode", "host"), ("container_name", "shared"), ("devices", ["/dev/a:/dev/a"])]:
            with self.subTest(key=key):
                config = json.loads(json.dumps(self.config))
                config["services"]["web"][key] = value
                with patch("check_project.docker", return_value=json.dumps(config)) as docker:
                    with self.assertRaises(ProjectError):
                        normalize_compose(check_project(self.root), self.root, "unique-check")
                self.assertEqual(docker.call_count, 1)

    def test_rejects_escaping_context(self) -> None:
        self.config["services"]["web"]["build"]["context"] = "/tmp"
        with patch("check_project.docker", return_value=json.dumps(self.config)):
            with self.assertRaises(ProjectError):
                normalize_compose(check_project(self.root), self.root, "unique-check")

    def test_readiness_failure_cleans_project_and_generated_image(self) -> None:
        def docker_result(arguments: list[str], **kwargs: object) -> str:
            if "config" in arguments:
                return json.dumps(self.config)
            if "port" in arguments:
                return "127.0.0.1:49152"
            return ""
        with (
            patch("check_project.docker", side_effect=docker_result) as docker,
            patch("check_project.wait_ready", side_effect=ProjectError("not ready")),
        ):
            with self.assertRaisesRegex(ProjectError, "not ready"):
                run_project(check_project(self.root), timeout=1)
        commands = [call.args[0] for call in docker.call_args_list]
        self.assertTrue(any("down" in command and "--volumes" in command for command in commands))
        self.assertEqual(commands[-1][:3], ["image", "rm", "-f"])

    def test_rejects_raw_includes_aliases_duplicates_and_malformed_mounts(self) -> None:
        cases = [
            "include: /tmp/private.yaml\nservices: {}",
            "services:\n  web: &web\n    image: redis:7\n  other: *web",
            "services:\n  web:\n    image: redis:7\n    image: redis:8",
            "services:\n  web:\n    image: redis:7\n    volumes: invalid",
            "services:\n  web:\n    image: redis:7\n    env_file: /tmp/private.env",
        ]
        for text in cases:
            with self.subTest(text=text):
                (self.root / "compose.portal.yaml").write_text(text)
                with patch("check_project.docker") as docker:
                    with self.assertRaises(ProjectError):
                        check_project(self.root)
                docker.assert_not_called()

    def test_nested_profile_resolves_context_relative_to_profile(self) -> None:
        nested = self.root / "nested"
        nested.mkdir()
        (nested / "Dockerfile").write_text("FROM python:3.12-slim")
        (nested / "compose.yaml").write_text("services:\n  web:\n    build: .\n")
        self.manifest["runtime"]["file"] = "nested/compose.yaml"
        (self.root / "portal-project.json").write_text(json.dumps(self.manifest))
        (self.root / "Dockerfile").unlink()
        self.assertEqual(check_project(self.root).compose_file, nested / "compose.yaml")

    def test_escapes_dollar_values_before_compose_reads_resolved_file(self) -> None:
        self.config["services"]["web"]["environment"] = {"PASSWORD": "literal$VALUE"}
        with patch("check_project.docker", return_value=json.dumps(self.config)):
            output = normalize_compose(check_project(self.root), self.root, "unique-check")
        resolved = json.loads(output.read_text())
        self.assertEqual(resolved["services"]["web"]["environment"]["PASSWORD"], "literal$$VALUE")

    def test_interrupt_also_cleans_project(self) -> None:
        def docker_result(arguments: list[str], **kwargs: object) -> str:
            if "config" in arguments:
                return json.dumps(self.config)
            if "up" in arguments:
                raise KeyboardInterrupt()
            return ""
        with patch("check_project.docker", side_effect=docker_result) as docker:
            with self.assertRaises(KeyboardInterrupt):
                run_project(check_project(self.root), timeout=1)
        commands = [call.args[0] for call in docker.call_args_list]
        self.assertTrue(any("down" in command for command in commands))

    def test_compose_missing_secrets_fails_before_any_docker(self) -> None:
        self.manifest["requiredEnv"] = ["TEST_COMPOSE_API_KEY"]
        (self.root / "portal-project.json").write_text(json.dumps(self.manifest))
        with patch.dict("os.environ", {}, clear=True), patch("check_project.docker") as docker:
            with self.assertRaisesRegex(ProjectError, "TEST_COMPOSE_API_KEY"):
                run_project(check_project(self.root))
        docker.assert_not_called()

    def test_accepts_compose_generated_empty_network_ipam(self) -> None:
        self.config["name"] = "fixture"
        self.config["networks"] = {"default": {"name": "fixture_default", "ipam": {}}}
        with patch("check_project.docker", return_value=json.dumps(self.config)):
            output = normalize_compose(check_project(self.root), self.root, "unique-check")
        self.assertEqual(json.loads(output.read_text())["networks"]["default"], {})
