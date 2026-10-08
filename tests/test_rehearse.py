import shutil
import json
from pathlib import Path

import pytest

import rehearse
from tests.fakes import FakeClient, text, tool_turn


@pytest.fixture
def broken_rehearsal(tmp_path, monkeypatch):
    """Every rehearsal test gets a known source, even after the learner repairs theirs."""
    source = Path(rehearse.__file__).resolve().parent
    fixture_root = tmp_path / "source"
    shutil.copytree(source / "capstone", fixture_root / "capstone")
    shutil.copyfile(source / "verify_capstone.py", fixture_root / "verify_capstone.py")
    reference = (source / "solutions" / "capstone_app.py").read_text()
    update_store = "        tasks[task_id] = updated\n"
    assert reference.count(update_store) == 1, "Reference solution's PATCH assignment changed"
    (fixture_root / "capstone" / "app.py").write_text(reference.replace(update_store, "", 1))
    monkeypatch.setattr(rehearse, "ROOT", fixture_root)
    return fixture_root


def test_build_client_loads_agent_env_file(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "AGENT_API_KEY=test-key\n"
        "AGENT_BASE_URL=https://example.test/v1\n"
        "AGENT_REQUEST_TIMEOUT=12\n"
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_API_KEY", raising=False)
    monkeypatch.delenv("AGENT_BASE_URL", raising=False)

    seen = {}

    class FakeOpenAI:
        def __init__(self, **kwargs):
            seen.update(kwargs)

    monkeypatch.setattr(rehearse, "OpenAI", FakeOpenAI)

    rehearse.build_client()

    assert seen == {
        "api_key": "test-key",
        "base_url": "https://example.test/v1",
        "timeout": 12.0,
    }


def test_one_run_copies_fixture_and_independently_verifies_repair(monkeypatch, broken_rehearsal):
    from pathlib import Path

    original_cwd = Path.cwd()
    source = Path(rehearse.__file__).resolve().parent
    workdirs = []

    def repair(client, messages, tools, registry, **kwargs):
        import re
        import shlex

        workdirs.append(Path.cwd())
        assert Path.cwd() != source
        assert Path("app.py").exists(), "Rehearsal must copy the repair fixture"
        assert Path("index.html").exists()
        assert Path("AGENTS.md").exists()
        prompt = messages[-1]["content"]
        assert str(broken_rehearsal / "verify_capstone.py") in prompt
        assert "Do not modify" in prompt
        command = re.search(r"```bash\n([^\n]+)\n```", prompt)
        assert command, "The verifier command must be separate from sentence punctuation"
        assert shlex.split(command.group(1))[-2:] == ["--project", "."]
        baseline = registry["run_bash"](command.group(1))
        assert "8/9 acceptance checks passed" in baseline
        assert "FAIL complete persistence" in baseline
        registry["write_file"]("app.py", (source / "solutions" / "capstone_app.py").read_text())
        return messages

    monkeypatch.setattr(rehearse, "run_agent", repair)
    assert rehearse.one_run(object()) is True
    assert Path.cwd() == original_cwd
    assert workdirs and not workdirs[0].exists()


def test_one_run_rejects_an_unrepaired_app_despite_success_report(monkeypatch, broken_rehearsal):
    monkeypatch.setattr(rehearse, "run_agent", lambda *args, **kwargs: [{"content": "Fixed!"}])
    assert rehearse.one_run(object()) is False


def test_one_run_cleans_temporary_directory_on_agent_exception(monkeypatch, broken_rehearsal):
    from pathlib import Path

    original_cwd = Path.cwd()
    workdirs = []

    def crash(*args, **kwargs):
        workdirs.append(Path.cwd())
        raise RuntimeError("Model request failed")

    monkeypatch.setattr(rehearse, "run_agent", crash)
    assert rehearse.one_run(object()) is False
    assert Path.cwd() == original_cwd
    assert workdirs and not workdirs[0].exists()


def test_one_run_stops_background_shell_processes(monkeypatch, broken_rehearsal):
    import os
    import shlex
    import sys
    import time

    pids = []

    def spawn_background(client, messages, tools, registry, **kwargs):
        result = registry["run_bash"](
            f"{shlex.quote(sys.executable)} -c 'import time; time.sleep(60)' "
            "> /dev/null 2>&1 & echo $!"
        )
        pids.append(int(result.splitlines()[-1]))
        raise RuntimeError("Stop the simulated model run")

    monkeypatch.setattr(rehearse, "run_agent", spawn_background)
    try:
        assert rehearse.one_run(object()) is False
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                os.kill(pids[0], 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            raise AssertionError("Rehearsal left a background process running")
    finally:
        if pids:
            try:
                os.kill(pids[0], 9)
            except ProcessLookupError:
                pass


def test_build_client_rejects_unbounded_timeouts(tmp_path, monkeypatch):
    import pytest

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENT_API_KEY", "test-key")
    for timeout in ["0", "-1", "301", "nan", "inf", "not-a-number"]:
        monkeypatch.setenv("AGENT_REQUEST_TIMEOUT", timeout)
        with pytest.raises(ValueError, match="AGENT_REQUEST_TIMEOUT"):
            rehearse.build_client()


def test_rehearsal_shell_caps_output_and_retains_failure_tail():
    import shlex
    import sys

    code = "import sys; print('x' * 8000); print('FINAL FAILURE', file=sys.stderr); sys.exit(7)"
    with rehearse.rehearsal_tools() as registry:
        result = registry["run_bash"](shlex.join([sys.executable, "-c", code]))
    assert result.startswith("exit 7\n")
    assert "FINAL FAILURE" in result
    assert "[truncated; showing last 6000" in result
    assert len(result) < 6200


def test_rehearsal_shell_caps_output_when_command_times_out():
    import shlex
    import sys

    code = "import time; print('x' * 8000, flush=True); print('BEFORE TIMEOUT', flush=True); time.sleep(60)"
    with rehearse.rehearsal_tools() as registry:
        result = registry["run_bash"](shlex.join([sys.executable, "-c", code]), timeout=0.1)
    assert result.startswith("exit timeout\n")
    assert "BEFORE TIMEOUT" in result
    assert "timed out" in result
    assert "[truncated; showing last 6000" in result
    assert len(result) < 6200


@pytest.mark.parametrize("baseline", ["repaired", "extra_failure"])
def test_invalid_baseline_stops_before_calling_agent(
    monkeypatch, broken_rehearsal, capsys, baseline,
):
    source = Path(rehearse.__file__).resolve().parent
    if baseline == "repaired":
        shutil.copyfile(source / "solutions" / "capstone_app.py",
                        broken_rehearsal / "capstone" / "app.py")
    else:
        (broken_rehearsal / "capstone" / "index.html").unlink()
    calls = []
    monkeypatch.setattr(rehearse, "run_agent", lambda *args, **kwargs: calls.append(args))

    assert rehearse.one_run(object()) is False
    assert calls == [], "An invalid baseline must not count as an agent repair attempt"
    output = capsys.readouterr().out.lower()
    assert "baseline invalid" in output
    assert "clean starter" in output


def test_failed_rehearsal_retains_tool_trace_and_checks(broken_rehearsal, tmp_path):
    artifacts = tmp_path / "evidence"
    client = FakeClient([
        tool_turn(("read-1", "read_file", {"path": "app.py"})),
        text("The task is complete."),
    ])

    assert rehearse.one_run(client, artifacts=artifacts) is False

    report = json.loads((artifacts / "report.json").read_text())
    assert report["outcome"] == "failed"
    assert report["stop_reason"] == "final_answer"
    assert report["model_turns"] == 2
    assert report["messages"][-1]["content"] == "The task is complete."
    result = next(message for message in report["messages"] if message["role"] == "tool")
    assert result["tool_call_id"] == "read-1"
    assert "def update_task" in result["content"]
    assert [check["name"] for check in report["final_checks"] if not check["passed"]] == [
        "complete persistence"
    ]
    assert (artifacts / "changes.diff").read_text() == ""


def test_rehearsal_distinguishes_configured_iteration_cap(broken_rehearsal, tmp_path, monkeypatch):
    monkeypatch.setattr(rehearse, "MAX_ITERS", 12, raising=False)
    artifacts = tmp_path / "evidence"
    client = FakeClient([
        tool_turn((f"read-{i}", "read_file", {"path": "app.py", "limit": 1}))
        for i in range(12)
    ])

    assert rehearse.one_run(client, artifacts=artifacts) is False
    report = json.loads((artifacts / "report.json").read_text())
    assert report["stop_reason"] == "iteration_limit"
    assert report["model_turns"] == 12


def test_rehearsal_retains_edits_and_partial_trace_on_error(
    broken_rehearsal, tmp_path,
):
    artifacts = tmp_path / "evidence"
    original = (broken_rehearsal / "capstone" / "app.py").read_text()
    # The second model request raises when the scripted client runs out of replies.
    client = FakeClient([tool_turn(("edit-1", "write_file", {
        "path": "app.py", "content": original + "\n# diagnostic marker\n",
    }))])

    assert rehearse.one_run(client, artifacts=artifacts) is False
    report = json.loads((artifacts / "report.json").read_text())
    assert report["outcome"] == "agent_error"
    assert report["stop_reason"] == "error"
    assert "scripted responses" in report["error"]
    assert report["messages"][-1]["tool_call_id"] == "edit-1"
    assert "+# diagnostic marker" in (artifacts / "changes.diff").read_text()
    assert (broken_rehearsal / "capstone" / "app.py").read_text() == original


def test_rehearsal_records_provider_stop_reason(broken_rehearsal, tmp_path):
    from types import SimpleNamespace

    # A provider can return no tool calls because its output limit was reached.
    response = SimpleNamespace(
        model="test-provider-model", usage=None,
        choices=[SimpleNamespace(message=text(""), finish_reason="length")],
    )
    client = SimpleNamespace(chat=SimpleNamespace(
        completions=SimpleNamespace(create=lambda **kwargs: response),
    ))
    artifacts = tmp_path / "evidence"

    assert rehearse.one_run(client, artifacts=artifacts) is False
    report = json.loads((artifacts / "report.json").read_text())
    assert report["model_responses"][0]["finish_reason"] == "length"
    assert report["model_responses"][0]["model"] == "test-provider-model"
