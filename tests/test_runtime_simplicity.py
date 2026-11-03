"""The supplied runner connects directly to learner functions and real tools."""
from copy import deepcopy
from io import StringIO

import pytest
from rich.console import Console

import main
import ui
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    'completed', Path(__file__).resolve().parents[1] / 'agent.py')
completed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(completed)
from tests.fakes import FakeClient, text, tool_turn


def test_ask_displays_request_without_replacing_sdk_client(monkeypatch):
    messages = [{"role": "user", "content": "Write FizzBuzz"}]
    shown = []
    monkeypatch.setattr(ui, "show_request", lambda history: shown.append(deepcopy(history)), raising=False)
    client = FakeClient([text("code")])
    answer = completed.ask(client, messages, [])
    assert shown == [messages]
    assert client.calls[0]["messages"] == messages
    assert answer.content == "code"




@pytest.mark.parametrize("allowed", [False, True])
def test_loop_checks_approval_before_executing_command(monkeypatch, allowed):
    executed = []
    asked = []
    def approve(command):
        asked.append(command)
        return allowed
    monkeypatch.setattr(ui, "approve_command", approve, raising=False)
    client = FakeClient([tool_turn(("check", "run_bash", {"command": "pytest -q"})), text("finished")])
    completed.run_agent(client, [], [], {"run_bash": lambda command: executed.append(command) or "exit 0\npassed"})
    assert asked == ["pytest -q"]
    assert executed == (["pytest -q"] if allowed else [])
    feedback = client.calls[1]["messages"][-1]
    assert feedback["tool_call_id"] == "check"
    assert feedback["content"] == ("exit 0\npassed" if allowed else "User declined to run this tool.")


def test_final_registration_contains_only_the_five_repair_tools():
    names = {"list_files", "read_file", "write_file", "str_replace", "run_bash"}
    assert set(completed.REGISTRY) == names
    assert {schema["function"]["name"] for schema in completed.TOOL_SCHEMAS} == names


def test_request_display_does_not_change_messages(monkeypatch):
    output = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=output, width=100))
    monkeypatch.setenv("AGENT_TRACE_MESSAGES", "1")
    messages = [{"role": "user", "content": "x" * 700}, text("reply")]
    original = deepcopy(messages)
    ui.show_request(messages)
    assert messages[0] == original[0]
    assert vars(messages[1]) == vars(original[1])
    assert "Roles: user -> assistant" in output.getvalue()
    assert "preview shortened" in output.getvalue()


@pytest.mark.parametrize("absolute", [False, True], ids=["relative-directory", "absolute-directory"])
def test_discovered_paths_can_be_read_without_reconstructing_them(tmp_path, monkeypatch, absolute):
    from tools import list_files

    evidence = tmp_path / "checkpoints"
    evidence.mkdir()
    (evidence / "release.md").write_text("Ready after checks pass", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    discovered = list_files(str(evidence) if absolute else "checkpoints").splitlines()
    assert len(discovered) == 1
    assert "Ready after checks pass" in completed.read_file(discovered[0])
    expected = str(evidence / "release.md") if absolute else "checkpoints/release.md"
    assert discovered[0] == expected




def test_hard_limit_does_not_leave_stopping_instructions_in_later_requests():
    messages = [{"role": "system", "content": "Use observed evidence."}]
    completed.remember(messages, "inspect")
    client = FakeClient([tool_turn(("read", "read_file", {"path": "note.md"})), text("done")])
    completed.run_agent(client, messages, [], {"read_file": lambda path: "actual evidence"}, max_iters=1)
    assert len(client.calls) == 1
    assert messages[-1]["role"] == "tool"
    completed.remember(messages, "continue")
    completed.run_agent(client, messages, [], {})
    system_messages = [message for message in client.calls[1]["messages"]
                       if isinstance(message, dict) and message["role"] == "system"]
    assert system_messages == [{"role": "system", "content": "Use observed evidence."}]
