"""The limitation comparisons must succeed only from real submitted evidence."""

import json
import socket
import sys
from pathlib import Path
from typing import Any

import pytest

from solutions.agent import run_agent
from solutions.tools import read_file


@pytest.fixture
def note(tmp_path: Path) -> str:
    path = tmp_path / "note.txt"
    path.write_text("\n".join(f"unique content {number}" for number in range(1, 9)), encoding="utf-8")
    return str(path)


def test_messages_mode_sends_only_the_question_without_reading(note: str) -> None:
    from checkpoints.limitations import run_read

    def forbidden_reader(**_: Any) -> str:
        pytest.fail("Messages-only mode must not read the file")

    result = run_read("messages", note, reader=forbidden_reader)

    assert result.requests[0]["messages"] == [{"role": "user", "content": result.prompt}]
    assert "unique content" not in json.dumps(result.requests)
    assert not result.observed_results
    assert not result.evidence_complete


def test_tool_mode_retries_the_same_question_and_submits_the_real_result(note: str) -> None:
    from checkpoints.limitations import run_read

    before = run_read("messages", note)
    after = run_read("tool", note, reader=read_file)

    assert after.prompt == before.prompt
    assert len(after.requests) == 2
    assert after.requests[0]["messages"] == before.requests[0]["messages"]
    assert after.requests[1]["messages"][-1] == {
        "role": "tool", "tool_call_id": "read-1", "content": read_file(note, limit=3),
    }
    assert after.visible_lines == [1, 2, 3]
    assert after.pending_ids == []
    assert after.evidence_complete


def test_unfinished_reader_is_an_error_not_evidence(note: str) -> None:
    from checkpoints.limitations import run_read

    def unfinished(**_: Any) -> str:
        raise NotImplementedError("Implement read_file")

    result = run_read("tool", note, reader=unfinished)
    assert "Error: Implement read_file" in result.requests[1]["messages"][-1]["content"]
    assert not result.visible_lines
    assert not result.evidence_complete


def test_submitted_tool_request_includes_the_assistant_role(note: str) -> None:
    from checkpoints.limitations import run_read

    result = run_read("tool", note, reader=read_file)
    submitted = json.loads(json.dumps(result.requests[1]["messages"], default=vars))

    assert submitted[1]["role"] == "assistant"
    assert submitted[1]["tool_calls"][0]["id"] == "read-1"


def test_paging_follows_the_actual_marker_to_find_line_six(note: str) -> None:
    from checkpoints.limitations import run_paging

    first = run_paging(1, note, reader=read_file)
    second = run_paging(4, note, reader=read_file)

    assert first.prompt == second.prompt
    assert first.visible_lines == [1, 2, 3]
    assert "continue with offset=4" in first.observed_results["read-1"]
    assert not first.evidence_complete
    assert second.visible_lines == [4, 5, 6]
    assert "6: unique content 6" in second.observed_results["read-1"]
    assert second.evidence_complete


def test_once_leaves_second_request_pending_but_loop_submits_both_pages(note: str) -> None:
    from checkpoints.limitations import run_loop_comparison

    once = run_loop_comparison("once", note, reader=read_file)
    loop = run_loop_comparison("loop", note, reader=read_file, run_loop=run_agent)

    assert once.prompt == loop.prompt
    assert len(once.requests) == 2
    assert len(loop.requests) == 3
    assert once.pending_ids == ["read-2"]
    assert list(once.observed_results) == ["read-1"]
    assert once.visible_lines == [1, 2, 3]
    assert not once.evidence_complete
    assert loop.pending_ids == []
    assert list(loop.observed_results) == ["read-1", "read-2"]
    assert loop.visible_lines == [1, 2, 3, 4, 5, 6]
    assert loop.evidence_complete
    for result in (once, loop):
        proposals = [message for message in result.requests[1]["messages"] if getattr(message, "tool_calls", None)]
        assert proposals[0].tool_calls[0].id == "read-1"
        assert json.loads(proposals[0].tool_calls[0].function.arguments) == {"path": note, "offset": 1, "limit": 3}


def test_prepared_final_answer_cannot_hide_missing_tool_feedback(note: str) -> None:
    from checkpoints.limitations import run_loop_comparison

    def answer_only(client: Any, messages: list[Any], tools: Any, registry: Any, **_: Any) -> list[Any]:
        for _ in range(3):
            messages.append(client.chat.completions.create(messages=messages, tools=tools).choices[0].message)
        return messages

    result = run_loop_comparison("loop", note, reader=read_file, run_loop=answer_only)
    assert not result.evidence_complete
    assert result.pending_ids == ["read-1", "read-2"]
    assert not result.observed_results


def test_forged_feedback_without_a_read_cannot_pass(note: str) -> None:
    from checkpoints.limitations import run_loop_comparison

    def forged_loop(client: Any, messages: list[Any], tools: Any, registry: Any, **_: Any) -> list[Any]:
        for _ in range(3):
            message = client.chat.completions.create(messages=messages, tools=tools).choices[0].message
            messages.append(message)
            for call in message.tool_calls or []:
                messages.append({"role": "tool", "tool_call_id": call.id, "content": read_file(note, **{key: value for key, value in json.loads(call.function.arguments).items() if key != "path"})})
        return messages

    result = run_loop_comparison("loop", note, reader=read_file, run_loop=forged_loop)
    assert not result.evidence_complete
    assert not result.observed_results


def test_reading_without_sending_feedback_is_incomplete(note: str) -> None:
    from checkpoints.limitations import run_loop_comparison

    def drops_feedback(client: Any, messages: list[Any], tools: Any, registry: Any, **_: Any) -> list[Any]:
        for _ in range(3):
            message = client.chat.completions.create(messages=messages, tools=tools).choices[0].message
            messages.append(message)
            for call in message.tool_calls or []:
                registry[call.function.name](**json.loads(call.function.arguments))
        return messages

    result = run_loop_comparison("loop", note, reader=read_file, run_loop=drops_feedback)
    assert not result.evidence_complete
    assert not result.observed_results


def test_loop_error_remains_visible_with_incomplete_evidence(note: str) -> None:
    from checkpoints.limitations import run_loop_comparison

    def unfinished(**_: Any) -> list[Any]:
        raise NotImplementedError("Implement the loop")

    result = run_loop_comparison("loop", note, reader=read_file, run_loop=unfinished)
    assert result.error == "NotImplementedError: Implement the loop"
    assert not result.evidence_complete


def test_offline_comparisons_never_build_a_client_or_open_a_socket(note: str, monkeypatch: pytest.MonkeyPatch) -> None:
    import main
    from checkpoints.limitations import run_loop_comparison, run_paging, run_read

    def forbidden(*_: Any, **__: Any) -> Any:
        pytest.fail("Offline checkpoints must not access the network")

    monkeypatch.setattr(main, "build_client", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.delenv("AGENT_API_KEY", raising=False)
    run_read("messages", note)
    run_read("tool", note, reader=read_file)
    run_paging(4, note, reader=read_file)
    run_loop_comparison("loop", note, reader=read_file, run_loop=run_agent)


@pytest.mark.parametrize("arguments", [["read", "--mode", "once"], ["loop", "--mode", "tool"]])
def test_cli_rejects_modes_for_a_different_comparison(arguments: list[str], monkeypatch: pytest.MonkeyPatch) -> None:
    from checkpoints.limitations import main

    monkeypatch.setattr(sys, "argv", ["limitations", *arguments])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2


def test_cli_messages_mode_prints_request_and_missing_evidence(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    from checkpoints.limitations import main

    monkeypatch.setattr(sys, "argv", ["limitations", "read", "--mode", "messages"])
    main()
    output = capsys.readouterr().out
    assert "MODEL REQUEST 1" in output
    assert "checkpoints/notes.txt" in output
    assert "OBSERVED TOOL RESULTS: none" in output
    assert "EVIDENCE COMPLETE: no" in output


def test_root_and_student_checkpoint_and_tests_are_identical() -> None:
    project = Path(__file__).resolve().parents[1]
    if project.name == "student" and project.parent.name == "docker-workshop":
        project = project.parents[1]
    student = project / "docker-workshop" / "student"
    if not student.is_dir():
        pytest.skip("The standalone student image has no repository mirror")
    for relative in ("checkpoints/limitations.py", "tests/test_limitations.py"):
        assert (project / relative).read_bytes() == (student / relative).read_bytes()
