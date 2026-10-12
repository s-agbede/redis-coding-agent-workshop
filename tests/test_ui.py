from io import StringIO

import pytest
from rich.console import Console

import ui


@pytest.fixture
def output(monkeypatch: pytest.MonkeyPatch) -> StringIO:
    stream = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=stream, force_terminal=False, width=100))
    return stream


def test_checkpoint_turn_display_groups_requests_and_literal_observations(output: StringIO) -> None:
    ui.show_turn(2)
    ui.show_tool_request("read-2", "read_file", '{"path":"[bold]notes.md", "offset":81}')
    ui.show_tool_result("read-2", "81: [bold]literal[/bold]\n82: next line")
    ui.show_answer("The file says **ready**.")
    shown = output.getvalue()
    assert "Model turn 2" in shown
    assert "REQUEST read-2" in shown
    assert '"offset": 81' in shown
    assert "[bold]notes.md" in shown
    assert "RESULT read-2" in shown
    assert "81: [bold]literal[/bold]" in shown
    assert "82: next line" in shown
    assert "characters, not tokens" in shown
    assert "Answer" in shown


def test_malformed_tool_arguments_remain_visible(output: StringIO) -> None:
    ui.show_tool_request("bad", "read_file", "{not json}")
    assert "{not json}" in output.getvalue()


@pytest.mark.parametrize("fenced", [False, True], ids=["plain-code", "markdown-code"])
def test_answer_preserves_code_lines_and_indentation(output: StringIO, fenced: bool) -> None:
    code = 'def fizzbuzz():\n    result = []\n    for n in range(1, 16):\n        result.append(str(n))\n    return result'
    answer = f"Here is the function:\n\n```python\n{code}\n```" if fenced else code + "\n\nExample:\nprint(fizzbuzz())\n# Example output"

    ui.show_answer(answer)

    # Ignore the panel frame, but keep all leading whitespace inside it.
    lines = [line[3:-3].rstrip() for line in output.getvalue().splitlines() if line.startswith("│")]
    first_line = next(line for line in lines if "def fizzbuzz():" in line)
    padding = " " * first_line.index("def fizzbuzz():")
    for code_line in code.splitlines():
        assert padding + code_line in lines
    if not fenced:
        assert "# Example output" in lines


def test_plain_answer_keeps_literal_markup_and_spacing(output: StringIO) -> None:
    ui.show_answer("First line\n    [bold]literal[/bold]\nLast line")
    shown = output.getvalue()
    assert "    [bold]literal[/bold]" in shown
    assert "First line     " in shown


@pytest.mark.parametrize("choice,expected", [("y", True), ("n", False)])
def test_command_approval_requires_explicit_response(output, monkeypatch, choice, expected):
    monkeypatch.delenv("AGENT_AUTO_APPROVE", raising=False)
    monkeypatch.setattr(ui.Prompt, "ask", lambda *args, **kwargs: choice)
    assert ui.approve_command("pytest -q") is expected
    assert "pytest -q" in output.getvalue()


def test_explicit_headless_approval_does_not_prompt(monkeypatch):
    monkeypatch.setenv("AGENT_AUTO_APPROVE", "1")
    monkeypatch.setattr(ui.Prompt, "ask", lambda *a, **kw: pytest.fail("Unexpected prompt"))
    assert ui.approve_command("pytest -q")


def test_command_result_is_displayed_once_without_changing_exit_status(output):
    ui.show_tool_result("check", "exit 3\nCheck failed [fixture]")
    assert output.getvalue().count("Check failed [fixture]") == 1
    assert "exit 3" in output.getvalue()
    assert "✓" not in output.getvalue()
