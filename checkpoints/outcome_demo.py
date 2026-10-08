"""Opening demonstration: a supplied agent repairs an isolated toy project.

The model replies and command approval are scripted; reading, editing, running
Python and checking its output are real. No student or capstone file is edited.
"""

import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from pydantic import BaseModel

from solutions.agent import run_agent
from solutions.tools import TOOL_SCHEMAS, read_file, str_replace
from tests.fakes import FakeClient, text, tool_turn


class DemoResult(BaseModel):
    before_source: str
    after_source: str
    before_output: str
    after_output: str
    baseline_passed: bool
    verified: bool
    tool_names: list[str]


def _run_script(project: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "greeting.py"], cwd=project,
        capture_output=True, text=True, timeout=5,
    )


def _show_trace(messages: list[Any]) -> list[str]:
    names: list[str] = []
    for message in messages:
        if isinstance(message, dict):
            if message.get("role") == "tool":
                print(f"RESULT {message['tool_call_id']}: {message['content']}")
            continue
        for call in message.tool_calls or []:
            names.append(call.function.name)
            print(f"REQUEST {call.id}: {call.function.name}({call.function.arguments})")
            if call.function.name == "run_bash":
                print("SCRIPTED APPROVAL: allow python greeting.py in the temporary project")
        if message.content:
            print(f"ASSISTANT: {message.content}")
    return names


def run_demo() -> DemoResult:
    """Execute completed-loop code using real operations in a temporary folder."""
    print("OFFLINE: scripted model replies and approval; real Python operations.")
    print("Using supplied completed code, not your unfinished exercise files.")
    print("TASK: make greeting.py print Hello, Ada! and run it to check.\n")
    with TemporaryDirectory(prefix="coding-agent-demo-") as directory:
        project = Path(directory)
        target = project / "greeting.py"
        before_source = 'print("Hello, Sam!")\n'
        target.write_text(before_source, encoding="utf-8")

        # These wrappers keep the demonstration's operations inside its toy file.
        def toy_file(path: str) -> Path:
            if path != "greeting.py":
                raise ValueError("This demonstration only operates on greeting.py")
            return target

        def read(path: str) -> str:
            return read_file(str(toy_file(path)))

        def edit(path: str, old_str: str, new_str: str) -> str:
            str_replace(str(toy_file(path)), old_str, new_str)
            return "Edited greeting.py"

        def run(command: str) -> str:
            if command != "python greeting.py":
                raise ValueError("Only python greeting.py is available in this demo")
            result = _run_script(project)
            return f"exit {result.returncode}\n{result.stdout}{result.stderr}".strip()

        baseline = _run_script(project)
        before_output = baseline.stdout.strip()
        baseline_passed = baseline.returncode == 0 and before_output == "Hello, Ada!"
        print(f"BASELINE: {'PASS' if baseline_passed else 'FAIL'} — expected Hello, Ada!; got {before_output}")
        client = FakeClient([
            tool_turn(("read-1", "read_file", {"path": "greeting.py"})),
            tool_turn(("edit-1", "str_replace", {
                "path": "greeting.py", "old_str": "Hello, Sam!", "new_str": "Hello, Ada!",
            })),
            tool_turn(("check-1", "run_bash", {"command": "python greeting.py"})),
            text("I changed the greeting and ran the script. Check the result independently."),
        ])
        registry = {"read_file": read, "str_replace": edit, "run_bash": run}
        schemas = [schema for schema in TOOL_SCHEMAS if schema["function"]["name"] in registry]
        messages = run_agent(
            client, [{"role": "user", "content": "Make greeting.py print Hello, Ada! and check it."}],
            schemas, registry,
        )
        print("\nRECORDED TOOL EXCHANGE (request, Python result, next request):")
        names = _show_trace(messages)
        checked = _run_script(project)
        after_output = checked.stdout.strip()
        verified = checked.returncode == 0 and after_output == "Hello, Ada!"
        after_source = target.read_text(encoding="utf-8")
        print(f"\nSOURCE BEFORE: {before_source.strip()}")
        print(f"SOURCE AFTER:  {after_source.strip()}")
        print(f"INDEPENDENT CHECK: {'PASS' if verified else 'FAIL'} — {after_output}")
        result = DemoResult(
            before_source=before_source, after_source=after_source,
            before_output=before_output, after_output=after_output,
            baseline_passed=baseline_passed, verified=verified, tool_names=names,
        )
    print("Temporary project removed. Your exercise files and task-list app are unchanged.")
    print("This explains the mechanism; a live model may choose different actions.")
    return result


if __name__ == "__main__":
    raise SystemExit(0 if run_demo().verified else 1)
