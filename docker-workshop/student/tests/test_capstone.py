"""The repair fixture and acceptance gate are exercised over real HTTP."""

import importlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

ROOT = Path(__file__).resolve().parents[1]


def verifier():
    assert (ROOT / "verify_capstone.py").exists(), "Acceptance verifier is missing"
    return importlib.import_module("verify_capstone")


def fixed_project(tmp_path: Path) -> Path:
    assert (ROOT / "capstone" / "app.py").exists(), "Repair fixture is missing"
    project = tmp_path / "capstone"
    shutil.copytree(ROOT / "capstone", project)
    shutil.copyfile(ROOT / "solutions" / "capstone_app.py", project / "app.py")
    return project


def broken_project(tmp_path: Path) -> Path:
    """Build the known defect independently of the learner's editable app."""
    project = fixed_project(tmp_path)
    app = project / "app.py"
    source = app.read_text()
    update_store = "        tasks[task_id] = updated\n"
    assert source.count(update_store) == 1, "Reference solution's PATCH assignment changed"
    app.write_text(source.replace(update_store, "", 1))
    return project


def request(url: str, method: str = "GET", body: object = None):
    data = json.dumps(body).encode() if body is not None else None
    with urlopen(Request(url, data=data, method=method,
                         headers={"Content-Type": "application/json"}), timeout=3) as response:
        raw = response.read()
        return response.status, json.loads(raw) if raw else None


def test_starter_fails_only_completion_persistence(tmp_path):
    checks = verifier().verify_project(broken_project(tmp_path))
    assert [check.name for check in checks if not check.passed] == [
        "complete persistence"
    ]
    assert "completed=true" in next(
        check.detail for check in checks if not check.passed
    )


def test_solution_passes_all_acceptance_checks(tmp_path):
    checks = verifier().verify_project(fixed_project(tmp_path))
    assert checks
    assert all(check.passed for check in checks), checks
    assert {"homepage", "create", "read", "complete persistence",
            "uncomplete persistence", "unknown ID", "cleanup"} <= {
                check.name for check in checks
            }


def test_repeated_checks_preserve_existing_tasks_and_stop_server(tmp_path):
    module = verifier()
    with module.running_app(fixed_project(tmp_path)) as url:
        assert not url.endswith(":8000")
        _, existing = request(url + "/tasks", "POST", {"title": "Keep my task"})
        for _ in range(2):
            assert all(check.passed for check in module.verify_url(url))
            assert request(url + "/tasks")[1] == [existing]
    with pytest.raises((URLError, ConnectionError, TimeoutError)):
        request(url + "/tasks")


def test_server_stops_when_verifier_caller_raises(tmp_path):
    with pytest.raises(RuntimeError, match="caller failed"):
        with verifier().running_app(fixed_project(tmp_path)) as url:
            raise RuntimeError("caller failed")
    with pytest.raises((URLError, ConnectionError, TimeoutError)):
        request(url + "/tasks")


def test_app_validates_titles_and_unknown_ids(tmp_path):
    with verifier().running_app(fixed_project(tmp_path)) as url:
        for title in ["", "   "]:
            with pytest.raises(HTTPError) as error:
                request(url + "/tasks", "POST", {"title": title})
            assert error.value.code == 422
        _, task = request(url + "/tasks", "POST", {"title": "  A task  "})
        assert task["title"] == "A task"
        for method in ["GET", "PATCH", "DELETE"]:
            with pytest.raises(HTTPError) as error:
                request(url + "/tasks/missing", method,
                        {"completed": True} if method == "PATCH" else None)
            assert error.value.code == 404


def test_cli_reports_real_failures_and_nonzero_exit(tmp_path):
    module = verifier()
    failed = subprocess.run(
        [sys.executable, str(ROOT / "verify_capstone.py"), "--project",
         str(broken_project(tmp_path / "broken"))],
        cwd=ROOT, capture_output=True, text=True, timeout=20,
    )
    assert failed.returncode == 1
    assert "FAIL complete persistence" in failed.stdout
    with module.running_app(fixed_project(tmp_path / "fixed")) as url:
        passed = subprocess.run(
            [sys.executable, str(ROOT / "verify_capstone.py"), "--url", url],
            cwd=tmp_path, capture_output=True, text=True, timeout=20,
        )
    assert passed.returncode == 0, passed.stdout + passed.stderr
    assert "PASS complete persistence" in passed.stdout


def test_launch_failure_has_readable_evidence(tmp_path):
    module = verifier()
    (tmp_path / "app.py").write_text("raise RuntimeError('cannot boot fixture')\n")
    checks = module.verify_project(tmp_path)
    assert len(checks) == 1
    assert checks[0].name == "server startup"
    assert not checks[0].passed
    assert "cannot boot fixture" in checks[0].detail


@pytest.mark.parametrize("changed_fields", [
    '{"title": "Wrong title"}',
    '{"completed": True}',
    '{"completed": "not-a-bool"}',
])
def test_failed_create_check_still_removes_its_task(tmp_path, changed_fields):
    module = verifier()
    project = fixed_project(tmp_path)
    source = project / "app.py"
    source.write_text(source.read_text().replace(
        "        tasks[task.id] = task\n        return task\n",
        "        tasks[task.id] = task\n"
        f"        return task.model_copy(update={changed_fields})\n",
    ))
    with module.running_app(project) as url:
        request(url + "/tasks", "POST", {"title": "Keep my task"})
        existing = request(url + "/tasks")[1]
        for _ in range(2):
            checks = module.verify_url(url)
            assert [check.name for check in checks if not check.passed] == ["create"]
            assert request(url + "/tasks")[1] == existing
            assert any(check.name == "cleanup" and check.passed for check in checks)
