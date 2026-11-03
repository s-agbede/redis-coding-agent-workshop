"""Exercise the progressive learner file without replacing its normal runner."""
import ast
import importlib.util
from pathlib import Path

import pytest

from tests.fakes import FakeClient, text, tool_turn

ROOT = Path(__file__).resolve().parents[1]


def load(path: Path):
    spec = importlib.util.spec_from_file_location("learner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module




def test_completed_file_retains_history_and_executes_actual_reader(tmp_path):
    learner = load(ROOT / "solutions/steps/03-playbook.py")
    note = tmp_path / "note.md"
    note.write_text("release evidence")
    client = FakeClient([tool_turn(("read", "read_file", {"path": str(note)})), text("done"), text("follow-up")])
    messages = []
    learner.remember(messages, "Find the release decision")
    learner.run_agent(client, messages, learner.TOOL_SCHEMAS, learner.REGISTRY)
    learner.remember(messages, "What supports that?")
    learner.run_agent(client, messages, learner.TOOL_SCHEMAS, learner.REGISTRY)
    assert client.calls[1]["messages"][-1] == {"role": "tool", "tool_call_id": "read", "content": "1: release evidence"}
    assert client.calls[2]["messages"][0]["content"] == "Find the release decision"
    assert client.calls[2]["messages"][-1]["content"] == "What supports that?"
