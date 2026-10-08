from pathlib import Path

import pytest

import check_setup


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in ("first_call.py", "tools.py", "agent.py", "verify_capstone.py", "capstone/app.py"):
        path = tmp_path / name
        path.parent.mkdir(exist_ok=True)
        path.touch()
    monkeypatch.setattr(check_setup.importlib.util, "find_spec", lambda name: object())
    return tmp_path


def test_offline_ready_does_not_claim_key_verified(workspace: Path) -> None:
    checks = check_setup.inspect_setup(workspace, {"AGENT_API_KEY": "private-test-value"})
    report = check_setup.format_report(checks)
    assert all(item.passed for item in checks)
    assert "private-test-value" not in report
    assert "not validated" in report
    assert "no model request" in report


def test_missing_key_directs_learners_to_instructor_for_live_access(workspace: Path) -> None:
    checks = check_setup.inspect_setup(workspace, {})
    report = check_setup.format_report(checks)
    assert not all(item.passed for item in checks)
    assert "AGENT_API_KEY" in report
    assert "instructor" in report.lower()
    assert "offline" not in report.lower()


def test_missing_dependency_has_recovery_command(workspace: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(check_setup.importlib.util, "find_spec", lambda name: None if name == "openai" else object())
    report = check_setup.format_report(check_setup.inspect_setup(workspace, {}))
    assert "MISSING" in report
    assert "openai" in report
    assert "uv sync" in report


def test_wrong_directory_explains_where_to_run(tmp_path: Path) -> None:
    report = check_setup.format_report(check_setup.inspect_setup(tmp_path, {}))
    assert "workshop root" in report


def test_placeholder_key_is_not_ready(workspace: Path) -> None:
    checks = check_setup.inspect_setup(workspace, {"AGENT_API_KEY": "your-api-key-here"})
    assert not all(item.passed for item in checks)
