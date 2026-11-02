"""Replay published edits and cumulative catch-ups in disposable workspaces.

Only tests substitute provider transport. All stages execute python main.py's
real main.py entry point and use real files and the learner's own registry.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


def replace_node(path: Path, replacement: str) -> None:
    source = path.read_text()
    new = ast.parse(replacement).body[0]
    def key(node):
        if isinstance(node, ast.FunctionDef):
            return node.name
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            return node.targets[0].id
        return None
    old = next(node for node in ast.parse(source).body if key(node) == key(new))
    lines = source.splitlines(keepends=True)
    lines[old.lineno - 1:old.end_lineno] = [replacement + "\n"]
    path.write_text("".join(lines))


@pytest.mark.parametrize("catch_up", [False, True], ids=["published-snippets", "solution-files"])
def test_single_agent_progression(tmp_path: Path, catch_up: bool):
    root = Path(__file__).resolve().parents[1]
    lessons = root / "docker-workshop/frontend/public/build-steps"
    source = root
    if not lessons.is_dir():
        pytest.skip("Published replay runs from the full repository")
    for name in ("agent.py", "main.py", "tools.py", "ui.py"):
        shutil.copy2(source / name, tmp_path / name)
    # Replay a fresh starter, never the learner's in-progress browser edits.
    shutil.copy2(root / "agent.py", tmp_path / "agent.py")
    for name in ("checkpoints", "tests", "solutions", "capstone"):
        shutil.copytree(source / name, tmp_path / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    env = {**os.environ, "PYTHONPATH": str(tmp_path), "PYTHONDONTWRITEBYTECODE": "1", "AGENT_API_KEY": "", "AGENT_AUTO_APPROVE": "", "AGENT_BASE_URL": "http://127.0.0.1:1"}

    def run(*args):
        result = subprocess.run([sys.executable, *args], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stdout + result.stderr
        return result.stdout

    def cli(replies, inputs, args=()):
        driver = '''
import io, json, runpy, sys
from contextlib import redirect_stdout
from unittest.mock import patch
import ui
from tests.fakes import FakeClient, text, tool_turn
spec = json.loads(sys.argv[1])
client = FakeClient([tool_turn(*r["calls"]) if "calls" in r else text(r["text"]) for r in spec["replies"]])
sys.argv = ["main.py", *spec["args"]]
output = io.StringIO()
with redirect_stdout(output), patch("openai.OpenAI", return_value=client), patch.object(ui, "prompt_user", side_effect=spec["inputs"]), patch.object(ui.Prompt, "ask", return_value="n"), patch("socket.create_connection", side_effect=AssertionError("No network in replay")):
    runpy.run_path("main.py", run_name="__main__")
print(json.dumps({"output": output.getvalue(), "requests": client.calls}, default=vars))
'''
        return json.loads(run("-c", driver, json.dumps({"replies": replies, "inputs": inputs, "args": args})))

    def apply(lesson, snapshot):
        if catch_up:
            shutil.copy2(tmp_path / "solutions/steps" / (snapshot + ".py"), tmp_path / "agent.py")
        else:
            for block in re.findall(r"```python\n(.*?)\n```", (lessons / lesson).read_text(), re.S):
                parsed = ast.parse(block)
                for node in parsed.body:
                    replacement = ast.get_source_segment(block, node)
                    replace_node(tmp_path / "agent.py", replacement)

    initial = cli([], ["hello"])
    assert "Implement ask in agent.py" in initial["output"]
    assert initial["requests"] == []
    first = "Write FizzBuzz for integers 1 to 15."
    follow = "Now change it to stop at 20."
    apply("01-first-call.md", "01-model")
    run("-m", "pytest", "tests/test_first_call.py", "-q")
    no_history = cli([{"text": "first code"}, {"text": "second code"}], [first, follow, "exit"])
    assert [m["role"] for m in no_history["requests"][1]["messages"]] == ["system", "user"]
    assert "tools" not in no_history["requests"][0]
    apply("03-conversation.md", "02-history")
    run("-m", "pytest", "tests/test_conversation.py", "-q")
    history = cli([{"text": "first code"}, {"text": "second code"}], [first, follow, "exit"])
    assert [m["role"] for m in history["requests"][1]["messages"]] == ["system", "user", "assistant", "user"]
    assert "REQUEST PREVIEW: 4 messages" in history["output"]
    # Advertise tools before implementing dispatch: visible pending action, no execution.
    replace_node(tmp_path / "agent.py", "TOOL_SCHEMAS = [LIST_SCHEMA, PLAIN_READ_SCHEMA]")
    question = "What's the latest release decision?"
    discover = {"calls": [["find", "list_files", {"path": "checkpoints"}]]}
    read = {"calls": [["read", "read_file", {"path": "checkpoints/release_log.md"}]]}
    pending = cli([discover], [question, "exit"])
    assert "Pending tool requests were not executed" in pending["output"]
    assert len(pending["requests"]) == 1
    apply("06-agent-loop.md", "03-loop")
    run("-m", "pytest", "tests/test_agent.py", "-q")
    blocked = cli([discover, read, {"text": "Cannot read yet"}], [question, "exit"])
    assert "release_log.md" in blocked["requests"][1]["messages"][-1]["content"]
    assert blocked["requests"][2]["messages"][-1]["content"] == "Error: Implement read_file in agent.py"
    apply("04-one-tool.md", "04-reader")
    run("-m", "pytest", "tests/test_read_file.py", "-q")
    plain = cli([discover, read, {"text": "Conditional release"}], [question, "exit"])
    assert "Release decision: Cedar is ready" in plain["requests"][2]["messages"][-1]["content"]
    assert "180:" not in plain["requests"][2]["messages"][-1]["content"]
    apply("05-better-tools.md", "05-paging")
    pages = [{"calls": [[f"page-{offset}", "read_file", {"path": "checkpoints/release_log.md", "offset": offset, "limit": 60}]]} for offset in (1, 61, 121, 181)]
    paged = cli([discover, *pages, {"text": "Conditional release"}], [question, "exit"])
    assert "continue with offset=61" in paged["requests"][2]["messages"][-1]["content"]
    assert "180: Release decision: Cedar is ready" in paged["requests"][4]["messages"][-1]["content"]
    assert "Model turn 6" in paged["output"]
    assert {s["function"]["name"] for s in paged["requests"][0]["tools"]} == {"list_files", "read_file"}
    apply("07-capstone.md", "06-repair")
    run("-m", "pytest", "tests/test_first_call.py", "tests/test_conversation.py", "tests/test_read_file.py", "tests/test_tools.py", "tests/test_agent.py", "-q")
    final = cli([{"calls": [["inspect", "read_file", {"path": "AGENTS.md"}]]}, {"text": "Inspected"}], ["Inspect project", "exit"], ["--project", "capstone"])
    assert "verify_capstone.py" in final["requests"][0]["messages"][0]["content"]
    assert "verify_capstone.py" in final["requests"][1]["messages"][-1]["content"]
    assert {s["function"]["name"] for s in final["requests"][0]["tools"]} == {"list_files", "read_file", "write_file", "str_replace", "run_bash"}

    denied = cli([{"calls": [["shell", "run_bash", {"command": "echo must-not-run"}]]}, {"text": "Check unverified"}], ["Run a check", "exit"], ["--project", "capstone"])
    assert denied["requests"][1]["messages"][-1] == {"role": "tool", "tool_call_id": "shell", "content": "User declined to run this tool."}
