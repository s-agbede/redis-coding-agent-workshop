from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console

import ui


@pytest.fixture
def output(monkeypatch: pytest.MonkeyPatch) -> StringIO:
    stream = StringIO()
    monkeypatch.setattr(ui, "console", Console(file=stream, force_terminal=False, width=100))
    monkeypatch.setattr(ui, "VERBOSE", False)
    return stream


def test_failed_command_shows_status_and_output_without_success_tick(output: StringIO) -> None:
    run = ui.wrap_registry({"run_bash": lambda **_: "exit 3\nCheck failed [fixture]"}, set())
    assert run["run_bash"](command="python check.py") == "exit 3\nCheck failed [fixture]"
    shown = output.getvalue()
    assert "exit 3" in shown
    assert "Check failed [fixture]" in shown
    assert "✓" not in shown


def test_successful_command_shows_exit_status(output: StringIO) -> None:
    run = ui.wrap_registry({"run_bash": lambda **_: "exit 0\n9/9 checks passed"}, set())
    run["run_bash"](command="python check.py")
    assert "exit 0" in output.getvalue()
    assert "9/9 checks passed" in output.getvalue()


def test_tool_exception_is_visible_and_still_reaches_the_loop(output: StringIO) -> None:
    def missing(**_: str) -> str:
        raise FileNotFoundError("missing.txt")

    run = ui.wrap_registry({"read_file": missing}, set())
    with pytest.raises(FileNotFoundError):
        run["read_file"](path="missing.txt")
    assert "missing.txt" in output.getvalue()
    assert "failed" in output.getvalue().lower()
    assert "✓" not in output.getvalue()


def test_denied_command_never_runs(output: StringIO, monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(**_: str) -> str:
        pytest.fail("Denied command executed")

    monkeypatch.setattr(ui.Prompt, "ask", lambda *a, **kw: "n")
    run = ui.wrap_registry({"run_bash": forbidden}, {"run_bash"}, ui.Approvals(auto=False))
    assert "declined" in run["run_bash"](command="anything")
    assert "✓" not in output.getvalue()


@pytest.mark.parametrize("verbose", [False, True])
def test_reader_observation_is_complete_only_in_verbose_mode(
    output: StringIO, monkeypatch: pytest.MonkeyPatch, verbose: bool,
) -> None:
    from solutions.tools import read_file

    monkeypatch.setattr(ui, "VERBOSE", verbose)
    path = Path(__file__).resolve().parents[1] / "checkpoints/release_log.md"
    expected = read_file(str(path), offset=170, limit=20)
    assert len(expected) > 200
    run = ui.wrap_registry({"read_file": read_file}, set())

    result = run["read_file"](path=str(path), offset=170, limit=20)

    assert result == expected
    shown = output.getvalue()
    assert "Reading" in shown
    if verbose:
        assert expected in shown
        assert "180: Release decision: Cedar is ready" in shown
        assert "continue with offset=190" in shown
    else:
        assert "170: Entry" not in shown
        assert "180: Release decision" not in shown
        assert "continue with offset=190" not in shown


def test_verbose_observation_is_literal_and_returned_unchanged(
    output: StringIO, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(ui, "VERBOSE", True)
    monkeypatch.setattr(ui, "console", Console(file=output, force_terminal=True, width=100))
    observation = "\n".join(f'[bold]line {number}[/bold] {{"ready": true}}' for number in range(20))
    run = ui.wrap_registry({"list_files": lambda **_: observation}, set())

    result = run["list_files"](path=".")

    assert result is observation
    assert observation in output.getvalue()


@pytest.mark.parametrize("verbose", [False, True])
def test_command_observation_keeps_its_labelled_output_tail(
    output: StringIO, monkeypatch: pytest.MonkeyPatch, verbose: bool,
) -> None:
    monkeypatch.setattr(ui, "VERBOSE", verbose)
    observation = "exit 0\ndiscarded start\n" + "\n".join(f"output line {number}: {'x' * 60}" for number in range(30))
    run = ui.wrap_registry({"run_bash": lambda **_: observation}, set())

    result = run["run_bash"](command="python check.py")

    assert result is observation
    shown = output.getvalue()
    assert "exit 0\n… [showing output tail]" in shown
    assert "discarded start" not in shown
    assert observation[-1200:] in shown
