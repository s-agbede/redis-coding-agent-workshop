"""Run the published copyable lessons against disposable learner workspaces."""

import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


def python_blocks(path: Path) -> list[str]:
    return re.findall(r"```python\n(.*?)\n```", path.read_text(encoding="utf-8"), flags=re.DOTALL)


def replace_function(path: Path, name: str, replacement: str) -> None:
    source = path.read_text(encoding="utf-8")
    node = next(item for item in ast.parse(source).body
                if isinstance(item, ast.FunctionDef) and item.name == name)
    lines = source.splitlines(keepends=True)
    lines[node.lineno - 1:node.end_lineno] = [replacement + "\n"]
    path.write_text("".join(lines), encoding="utf-8")


@pytest.mark.parametrize("starter", ["", "docker-workshop/student"])
@pytest.mark.parametrize("catch_up", [False, True], ids=["published-snippets", "solution-files"])
def test_published_lessons_run_from_first_call_through_agent_loop(
    tmp_path: Path, starter: str, catch_up: bool,
) -> None:
    root = Path(__file__).resolve().parents[1]
    lessons = root / "docker-workshop/frontend/public/build-steps"
    source = root / starter
    if not lessons.is_dir() or not source.is_dir():
        pytest.skip("Published lesson replay runs in the full repository")
    for name in ("first_call.py", "request_trace.py", "agent.py", "tools.py", "main.py", "ui.py"):
        shutil.copy2(source / name, tmp_path / name)
    for name in ("checkpoints", "tests", "solutions"):
        shutil.copytree(source / name, tmp_path / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    environment = {
        **os.environ, "PYTHONPATH": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1",
        "AGENT_API_KEY": "", "AGENT_BASE_URL": "http://127.0.0.1:1",
    }

    def run(*arguments: str) -> str:
        result = subprocess.run(
            [sys.executable, *arguments], cwd=tmp_path, env=environment,
            capture_output=True, text=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def run_cli(
        module: str,
        arguments: list[str],
        responses: list[dict[str, Any]],
        user_inputs: list[str] | None = None,
    ) -> dict[str, Any]:
        """Exercise the real CLI; substitute transport only inside this test."""
        driver = '''
import importlib
import io
import json
import sys
from contextlib import ExitStack, redirect_stdout
from unittest.mock import patch
from tests.fakes import FakeClient, text, tool_turn

spec = json.loads(sys.argv[1])
module = importlib.import_module(spec["module"])
responses = [tool_turn(*reply["calls"]) if "calls" in reply else text(reply["text"])
             for reply in spec["responses"]]
client = FakeClient(responses)
factory = "OpenAI" if spec["module"] == "first_call" else "build_client"
sys.argv = [spec["module"], *spec["arguments"]]
output = io.StringIO()
with redirect_stdout(output), ExitStack() as patches:
    patches.enter_context(patch.object(module, factory, return_value=client))
    patches.enter_context(patch("builtins.input", return_value=""))
    patches.enter_context(patch("socket.create_connection", side_effect=AssertionError("No network in lesson replay")))
    if spec["user_inputs"] is not None:
        patches.enter_context(patch.object(module.ui, "prompt_user", side_effect=spec["user_inputs"]))
    module.main()
print(json.dumps({"output": output.getvalue(), "requests": client.calls}, default=vars))
'''
        specification = {"module": module, "arguments": arguments,
                         "responses": responses, "user_inputs": user_inputs}
        return json.loads(run("-c", driver, json.dumps(specification)))

    def apply(lesson: str, target: str, name: str, solution: str | None = None) -> None:
        if catch_up and solution:
            shutil.copy2(tmp_path / solution, tmp_path / target)
        else:
            blocks = python_blocks(lessons / lesson)
            snippet = next(block for block in blocks if block.startswith(f"def {name}("))
            replace_function(tmp_path / target, name, snippet)

    apply("01-first-call.md", "first_call.py", "ask", "solutions/first_call.py")
    assert "2 passed" in run("-m", "pytest", "tests/test_first_call.py", "-q")
    first_call = run_cli("first_call", [], [{"text": "test transport reply"}])
    first_prompt = first_call["requests"][0]["messages"][0]["content"]
    assert "FizzBuzz" in first_prompt
    assert "ASSISTANT: test transport reply" in first_call["output"]
    assert "REQUEST PREVIEW" not in first_call["output"]

    follow_up = "Now change it to stop at 20."
    latest = run_cli("first_call", ["--show-messages", "--prompt", follow_up], [{"text": "test reply"}])
    latest_request = latest["requests"][0]["messages"]
    assert len(latest_request) == 1
    assert "REQUEST PREVIEW: 1 message" in latest["output"]
    assert f"[1] user: {follow_up}" in latest["output"]
    apply("03-conversation.md", "checkpoints/stage1_chat.py", "chat_turn", "solutions/stage1_chat.py")
    assert "3 passed" in run("-m", "pytest", "tests/test_conversation.py", "-q")
    retained = run_cli("checkpoints.stage1_chat", ["--show-messages"], [{"text": "first reply"}, {"text": "second reply"}],
                       [first_prompt, follow_up, "exit"])
    retained_request = retained["requests"][1]["messages"]
    assert len(retained_request) == 3
    assert latest_request[-1] == retained_request[-1]
    assert "REQUEST PREVIEW: 3 messages\nRoles: user -> assistant -> user" in retained["output"]
    assert "[2] assistant: first reply" in retained["output"]
    restarted = run_cli("checkpoints.stage1_chat", ["--show-messages"], [{"text": "test reply"}], [follow_up, "exit"])
    assert len(restarted["requests"][0]["messages"]) == 1
    assert "REQUEST PREVIEW: 1 message" in restarted["output"]
    assert "[2] assistant:" not in restarted["output"]

    # The plain reader is deliberately applied before its bounded replacement.
    apply("04-one-tool.md", "tools.py", "read_file")
    assert "2 passed" in run("-m", "pytest", "tests/test_read_file.py", "-q")
    brief_run = run_cli("checkpoints.stage2_one_tool", [], [
        {"calls": [["read-1", "read_file", {"path": "checkpoints/project_brief.md"}]]},
        {"text": "test reply"},
    ])
    brief = brief_run["output"]
    assert "Release name: Cedar." in brief
    assert brief.index("REQUEST read-1") < brief.index("HARNESS: Python") < brief.index("RESULT read-1")
    prompt = ("Read checkpoints/release_log.md. What release decision is recorded near line 180? "
              "If range selection is available, read offset=170, limit=20.")
    plain_run = run_cli("checkpoints.stage2_one_tool", ["--prompt", prompt], [
        {"calls": [["read-1", "read_file", {"path": "checkpoints/release_log.md"}]]},
        {"text": "test reply"},
    ])
    plain = plain_run["output"]
    assert len(plain.splitlines()) > 200
    assert "Release decision: Cedar is ready" in plain

    apply("05-better-tools.md", "tools.py", "read_file", "solutions/tools.py")
    assert "passed" in run("-m", "pytest", "tests/test_read_file.py", "tests/test_tools.py", "-q")
    paged_run = run_cli("checkpoints.stage2_one_tool", ["--prompt", prompt, "--paged"], [
        {"calls": [["read-1", "read_file", {"path": "checkpoints/release_log.md", "offset": 170, "limit": 20}]]},
        {"text": "test reply"},
    ])
    paged = paged_run["output"]
    assert f"PROMPT: {prompt}" in plain and f"PROMPT: {prompt}" in paged
    assert plain_run["requests"][0]["messages"] == paged_run["requests"][0]["messages"]
    assert "180: Release decision: Cedar is ready" in paged
    assert "continue with offset=190" in paged
    assert len(paged) < len(plain)
    next_page = run_cli("checkpoints.stage2_one_tool", ["--prompt", prompt, "--paged"], [
        {"calls": [["read-1", "read_file", {"path": "checkpoints/release_log.md", "offset": 190, "limit": 20}]]},
        {"text": "test reply"},
    ])
    assert "200:" in next_page["output"]

    agent_path = tmp_path / "agent.py"
    if catch_up:
        shutil.copy2(tmp_path / "solutions/agent.py", agent_path)
    else:
        code = agent_path.read_text(encoding="utf-8")
        blocks = python_blocks(lessons / "06-agent-loop.md")
        replacements = (
            ('        raise NotImplementedError("Add the stopping rule")', "if not msg.tool_calls:"),
            ('                raise NotImplementedError("Add tool dispatch")', "result = registry["),
            ('            raise NotImplementedError("Add tool feedback")', "messages.append({"),
        )
        for marker, prefix in replacements:
            snippet = next(block for block in blocks if block.lstrip().startswith(prefix))
            if marker in code:
                code = code.replace(marker, snippet, 1)
            else:
                assert snippet in code, "A completed catch-up file must match the published snippet"
        agent_path.write_text(code, encoding="utf-8")
    assert "9 passed" in run("-m", "pytest", "tests/test_agent.py", "-q")
    assert "RESULT retry:" in run("-m", "checkpoints.recovery")
