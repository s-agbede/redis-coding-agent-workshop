import importlib
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.parametrize("prompt", [None, "Now change it to stop at 20."])
@pytest.mark.parametrize("module_name", ["first_call", "solutions.first_call"])
@pytest.mark.parametrize("show_messages", [False, True])
def test_first_call_cli_sends_source_prompt_or_explicit_override(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    prompt: str | None, module_name: str, show_messages: bool,
) -> None:
    import sys
    from solutions.first_call import ask
    from tests.fakes import FakeClient, text

    first_call = importlib.import_module(module_name)
    client = FakeClient([text("reply supplied by the test transport")])
    monkeypatch.setattr(first_call, "OpenAI", lambda **kwargs: client)
    monkeypatch.setattr(first_call, "ask", ask)
    arguments = ["--prompt", prompt] if prompt is not None else []
    if show_messages:
        arguments.append("--show-messages")
    monkeypatch.setattr(sys, "argv", ["first_call.py", *arguments])
    first_call.main()
    expected_prompt = prompt if prompt is not None else first_call.FIZZBUZZ_PROMPT
    assert client.calls[0]["messages"] == [{"role": "user", "content": expected_prompt}]
    output = capsys.readouterr().out
    assert f"PROMPT: {expected_prompt}" in output
    assert "ASSISTANT: reply supplied by the test transport" in output
    if show_messages:
        assert "REQUEST PREVIEW: 1 message" in output
        assert f"Roles: user\n[1] user: {expected_prompt}" in output
        assert output.index("REQUEST PREVIEW") < output.index("ASSISTANT:")
    else:
        assert "REQUEST PREVIEW" not in output


def test_first_call_rejects_the_removed_scripted_route(monkeypatch):
    import sys
    import first_call
    from solutions.first_call import ask

    monkeypatch.setattr(first_call, "ask", ask)
    monkeypatch.setattr(sys, "argv", ["first_call.py", "--offline"])
    with pytest.raises(SystemExit) as error:
        first_call.main()
    assert error.value.code == 2


def test_first_call_client_uses_environment_configuration(monkeypatch):
    import sys
    import first_call
    from solutions.first_call import ask
    from tests.fakes import FakeClient, text

    seen = {}

    def build_client(**kwargs):
        seen.update(kwargs)
        return FakeClient([text("prepared reply")])

    monkeypatch.setenv("AGENT_API_KEY", "test-only-key")
    monkeypatch.setenv("AGENT_BASE_URL", "https://example.test/v1")
    monkeypatch.setattr(first_call, "OpenAI", build_client)
    monkeypatch.setattr(first_call, "ask", ask)
    monkeypatch.setattr(sys, "argv", ["first_call.py"])
    first_call.main()
    assert seen == {"api_key": "test-only-key", "base_url": "https://example.test/v1"}


@pytest.mark.parametrize("module_name", ["checkpoints.stage1_chat", "solutions.stage1_chat"])
@pytest.mark.parametrize("show_messages", [False, True])
def test_chat_cli_retains_history_and_starts_a_fresh_session(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
    module_name: str, show_messages: bool,
) -> None:
    import sys
    from openai.types.chat import ChatCompletionMessage
    from first_call import FIZZBUZZ_PROMPT
    from solutions.stage1_chat import chat_turn
    from tests.fakes import FakeClient, text

    stage1_chat = importlib.import_module(module_name)
    monkeypatch.setattr(stage1_chat, "chat_turn", chat_turn)
    arguments = ["--show-messages"] if show_messages else []
    monkeypatch.setattr(sys, "argv", ["stage1_chat", *arguments])
    first = FakeClient([ChatCompletionMessage(role="assistant", content="first reply"), text("second reply")])
    restarted = FakeClient([text("fresh-session reply")])
    clients = iter([first, restarted])
    monkeypatch.setattr(stage1_chat, "build_client", lambda: next(clients))
    follow_up = "Now change it to stop at 20."
    user_inputs = iter([FIZZBUZZ_PROMPT, follow_up, "exit", follow_up, "exit"])
    monkeypatch.setattr(stage1_chat.ui, "prompt_user", lambda: next(user_inputs))
    answers = []
    monkeypatch.setattr(stage1_chat.ui, "show_answer", answers.append)

    stage1_chat.main()
    stage1_chat.main()

    assert first.calls[0]["messages"] == [{"role": "user", "content": FIZZBUZZ_PROMPT}]
    second_request = first.calls[1]["messages"]
    assert len(second_request) == 3
    assert second_request[0]["content"] == FIZZBUZZ_PROMPT
    assert second_request[1].role == "assistant" and second_request[1].content == "first reply"
    assert second_request[-1] == {"role": "user", "content": follow_up}
    assert restarted.calls[0]["messages"] == [{"role": "user", "content": follow_up}]
    assert answers == ["first reply", "second reply", "fresh-session reply"]
    output = capsys.readouterr().out
    if show_messages:
        headers = [line for line in output.splitlines() if line.startswith("REQUEST PREVIEW:")]
        assert headers == ["REQUEST PREVIEW: 1 message", "REQUEST PREVIEW: 3 messages", "REQUEST PREVIEW: 1 message"]
        assert "Roles: user -> assistant -> user" in output
        assert "[2] assistant: first reply" in output
        assert f"[3] user: {follow_up}" in output
        restarted_preview = output.rsplit("REQUEST PREVIEW:", maxsplit=1)[1]
        assert f"[1] user: {follow_up}" in restarted_preview
        assert "first reply" not in restarted_preview
        assert FIZZBUZZ_PROMPT not in restarted_preview
    else:
        assert "REQUEST PREVIEW" not in output


def test_request_preview_precedes_forwarding_and_preserves_arguments_and_response(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from copy import deepcopy
    from types import SimpleNamespace

    from openai.types.chat import ChatCompletionMessage
    from request_trace import with_request_preview

    messages = [
        {"role": "user", "content": "Write FizzBuzz."},
        ChatCompletionMessage(role="assistant", content="Here is the function."),
        {"role": "user", "content": "Now change it to stop at 20."},
    ]
    original_messages = deepcopy(messages)
    headers = {"Authorization": "test-only-secret"}
    response = object()
    forwarded: dict[str, Any] = {}
    preview = ""

    def create(**kwargs: Any) -> object:
        nonlocal preview
        preview = capsys.readouterr().out
        forwarded.update(kwargs)
        return response

    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    request = {"model": "test-model", "messages": messages, "temperature": 0.25, "extra_headers": headers}

    result = with_request_preview(client).chat.completions.create(**request)

    assert result is response
    assert forwarded.keys() == request.keys()
    assert all(forwarded[key] is value for key, value in request.items())
    assert messages == original_messages
    assert "REQUEST PREVIEW: 3 messages\nRoles: user -> assistant -> user" in preview
    assert "[1] user: Write FizzBuzz." in preview
    assert "[2] assistant: Here is the function." in preview
    assert "[3] user: Now change it to stop at 20." in preview
    assert "test-only-secret" not in preview and "Authorization" not in preview
    assert "test-model" not in preview and "temperature" not in preview
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("content", [None, "", "a" * 600, "a" * 600 + "Z"], ids=["none", "empty", "600-characters", "601-characters"])
@pytest.mark.parametrize("sdk_message", [False, True], ids=["dictionary", "sdk-object"])
def test_request_preview_shortens_only_display_after_600_characters(
    capsys: pytest.CaptureFixture[str], content: str | None, sdk_message: bool,
) -> None:
    from openai.types.chat import ChatCompletionMessage
    from request_trace import with_request_preview
    from tests.fakes import FakeClient, text

    message = (ChatCompletionMessage(role="assistant", content=content) if sdk_message
               else {"role": "assistant", "content": content})
    messages = [message]
    client = FakeClient([text("reply")])

    with_request_preview(client).chat.completions.create(model="test", messages=messages)

    output = capsys.readouterr().out
    assert f"[1] assistant: {(content or '')[:600]}\n" in output
    assert "Z" not in output
    assert ("[preview shortened; full content sent]" in output) == (len(content or "") > 600)
    assert client.calls[0]["messages"] == messages


def test_chat_cli_rejects_the_removed_scripted_route(monkeypatch):
    import sys
    from checkpoints import stage1_chat
    from solutions.stage1_chat import chat_turn

    monkeypatch.setattr(stage1_chat, "chat_turn", chat_turn)
    monkeypatch.setattr(sys, "argv", ["stage1_chat", "--offline"])
    with pytest.raises(SystemExit) as error:
        stage1_chat.main()
    assert error.value.code == 2


def test_history_comparison_changes_context_but_keeps_the_question():
    from checkpoints import history

    assert hasattr(history, "question_request"), "Need separately runnable before/after requests"
    latest = history.question_request(remember=False)
    retained = history.question_request(remember=True)
    assert latest.messages[-1] == retained.messages[-1]
    assert len(latest.messages) == 1
    assert len(retained.messages) == 3
    assert "Cedar" not in latest.model_dump_json()
    assert "Cedar" in retained.model_dump_json()
    retained.messages[0].content = "changed"
    assert "Cedar" in history.question_request(remember=True).model_dump_json()


def test_history_modes_run_separately_without_calling_a_model(tmp_path):
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "AGENT_API_KEY": "", "PYTHONPATH": str(root)}
    for mode, evidence in (("latest", "PROJECT NAME IN REQUEST: missing"), ("retained", "PROJECT NAME IN REQUEST: present")):
        result = subprocess.run(
            [sys.executable, "-m", "checkpoints.history", "--mode", mode],
            cwd=tmp_path, env=environment, capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, result.stderr
        assert evidence in result.stdout
        assert "What is my project's name?" in result.stdout
        assert "No request is sent to a model" in result.stdout


def test_history_shows_what_is_sent_again_and_what_restart_loses():
    from checkpoints.history import history_requests

    first, second, restarted = history_requests()
    assert [item.role for item in first.messages] == ["user"]
    assert "Cedar" in first.messages[0].content
    assert [item.role for item in second.messages] == ["user", "assistant", "user"]
    assert second.messages[0] == first.messages[0]
    assert [item.role for item in restarted.messages] == ["user"]
    assert restarted.messages[0] == second.messages[-1]
    assert "Cedar" not in restarted.model_dump_json()


def test_outcome_demo_really_repairs_and_checks_a_temporary_project(tmp_path, monkeypatch, capsys):
    from checkpoints.outcome_demo import run_demo

    monkeypatch.chdir(tmp_path)
    existing = tmp_path / "greeting.py"
    existing.write_text("Do not edit learner files.\n")
    result = run_demo()

    assert result.before_output == "Hello, Sam!"
    assert result.after_output == "Hello, Ada!"
    assert result.baseline_passed is False
    assert result.verified is True
    assert "Sam" in result.before_source and "Ada" in result.after_source
    assert result.tool_names == ["read_file", "str_replace", "run_bash"]
    assert existing.read_text() == "Do not edit learner files.\n"
    assert list(tmp_path.iterdir()) == [existing]
    output = capsys.readouterr().out
    assert "OFFLINE" in output and "scripted" in output
    assert "BASELINE: FAIL" in output and "INDEPENDENT CHECK: PASS" in output
    for call_id in ("read-1", "edit-1", "check-1"):
        assert f"REQUEST {call_id}" in output
        assert f"RESULT {call_id}" in output
    assert output.index("REQUEST check-1") < output.index("SCRIPTED APPROVAL") < output.index("RESULT check-1")


def test_examples_run_without_provider_configuration(tmp_path):
    import os
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "AGENT_API_KEY": "", "AGENT_BASE_URL": "http://127.0.0.1:1", "PYTHONPATH": str(root)}
    for module, expected in (
        ("checkpoints.history", "AFTER RESTART"),
        ("checkpoints.outcome_demo", "INDEPENDENT CHECK: PASS"),
    ):
        result = subprocess.run(
            [sys.executable, "-m", module], cwd=tmp_path, env=environment,
            capture_output=True, text=True, timeout=15,
        )
        assert result.returncode == 0, result.stderr
        assert expected in result.stdout
        assert "OFFLINE" in result.stdout
