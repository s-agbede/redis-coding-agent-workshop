"""Scripted model + real tools: missing file, recovery, denial, execution failure.

Run after completing the loop: uv run python -m checkpoints.recovery
"""

import shlex
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from agent import run_agent
from tests.fakes import FakeClient, text, tool_turn
from tools import TOOL_SCHEMAS, read_file, run_bash


def run_recovery(
    directory: Path,
    run_loop: Callable[..., list[Any]] = run_agent,
    reader: Callable[..., str] = read_file,
) -> list[Any]:
    fixture = directory / "note.txt"
    fixture.write_text("You found the right file.\n", encoding="utf-8")
    command = f"{shlex.quote(sys.executable)} -c {shlex.quote('raise SystemExit(3)')}"
    client = FakeClient([
        tool_turn(("missing", "read_file", {"path": str(directory / "missing.txt")})),
        tool_turn(("retry", "read_file", {"path": str(fixture)})),
        tool_turn(("denied", "run_bash", {"command": "echo this must not execute"})),
        tool_turn(("failed", "run_bash", {"command": command})),
        text("Read the corrected path. One action was declined; the approved check exited 3. Task not verified."),
    ])
    decisions = iter([False, True])

    def gated_command(command: str) -> str:
        if not next(decisions):
            return "User declined to run this tool."
        return run_bash(command)

    return run_loop(
        client, [{"role": "user", "content": "Read the note, then check the task."}],
        TOOL_SCHEMAS, {"read_file": reader, "run_bash": gated_command},
    )


def main() -> None:
    print("OFFLINE: scripted model responses and approval decisions; real file and process tools.")
    with tempfile.TemporaryDirectory(prefix="agent-recovery-") as directory:
        messages = run_recovery(Path(directory))
    for message in messages:
        if isinstance(message, dict) and message.get("role") == "tool":
            print(f"RESULT {message['tool_call_id']}: {message['content']}")
        elif getattr(message, "tool_calls", None):
            for call in message.tool_calls:
                print(f"REQUEST {call.id}: {call.function.name}({call.function.arguments})")
        elif getattr(message, "content", None):
            print(f"ANSWER: {message.content}")


if __name__ == "__main__":
    main()
