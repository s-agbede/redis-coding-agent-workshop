"""Real disposable tmux sessions; no provider calls or learner workspace edits."""

import shlex
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from collections.abc import Callable, Iterator
from tempfile import TemporaryDirectory

import pytest
from terminal import TerminalDispatcher


HOOK = Path(__file__).resolve().parents[2] / "docker/guided/terminal.bash"


def wait_for(predicate: Callable[[], bool], timeout: float = 4) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.02)
    raise AssertionError("Terminal did not reach the expected state")


@pytest.fixture
def terminal(tmp_path: Path) -> Iterator[tuple[TerminalDispatcher, Path]]:
    assert HOOK.is_file(), "The shared shell needs a readiness hook"
    if shutil.which("tmux") is None:
        pytest.skip("tmux is required for terminal integration tests")
    version = subprocess.run(["bash", "-c", "echo ${BASH_VERSINFO[0]}"], capture_output=True, text=True, check=True)
    if int(version.stdout.strip()) < 4:
        pytest.skip("The guided runtime uses Bash 4+ readline; run these checks in that container")
    socket_dir = TemporaryDirectory(prefix="workshop-tmux-", dir="/tmp")
    socket = Path(socket_dir.name) / "socket"
    prefix = ("tmux", "-S", str(socket))
    directory = tmp_path / "requests"
    directory.mkdir(mode=0o700)
    shell = f"WORKSHOP_RUN_DIR={shlex.quote(str(directory))} exec bash --noprofile --rcfile {shlex.quote(str(HOOK))} -i"
    subprocess.run([*prefix, "-f", "/dev/null", "new-session", "-d", "-s", "review", "-c", str(tmp_path), shell], check=True)
    dispatcher = TerminalDispatcher(directory=directory, target="review:0.0", tmux=prefix)
    try:
        try:
            wait_for(dispatcher.ready)
        except AssertionError as error:
            state = dispatcher.tmux_command("display-message", "-p", "-t", dispatcher.target, "#{pane_current_command}|#{@workshop_ready}|#{pane_in_mode}|#{pane_pid}|#{@workshop_shell_pid}")
            output = dispatcher.tmux_command("capture-pane", "-p", "-t", dispatcher.target)
            raise AssertionError(f"Shell state: {state}\n{output}") from error
        yield dispatcher, tmp_path
    finally:
        subprocess.run([*prefix, "kill-server"], check=False, capture_output=True)
        socket_dir.cleanup()


def test_shell_hook_is_packaged() -> None:
    assert HOOK.is_file(), "The shared shell needs a readiness hook"


def test_runs_exact_multiline_command_in_the_visible_shell(terminal: tuple[TerminalDispatcher, Path]) -> None:
    dispatcher, directory = terminal
    command = "printf 'café\\n' > first.txt\nprintf '%s\\n' \"$PWD\" > second.txt\n"
    dispatcher.run(command)
    wait_for(lambda: (directory / "second.txt").exists())
    assert (directory / "first.txt").read_text() == "café\n"
    assert (directory / "second.txt").read_text().strip() == str(directory)
    output = dispatcher.tmux_command("capture-pane", "-p", "-t", dispatcher.target)
    assert "printf" in output and "first.txt" in output


def test_refuses_interactive_program_without_sending_command(terminal: tuple[TerminalDispatcher, Path]) -> None:
    from terminal import TerminalBusy

    dispatcher, directory = terminal
    dispatcher.run("python3 -q")
    wait_for(lambda: not dispatcher.ready())
    with pytest.raises(TerminalBusy):
        dispatcher.run("print('SHOULD_NOT_REACH_PYTHON')")
    output = dispatcher.tmux_command("capture-pane", "-p", "-t", dispatcher.target)
    assert "SHOULD_NOT_REACH_PYTHON" not in output


@pytest.mark.parametrize("command,process", [
    ('python3 -c "input(\'Interrupt recovery check: \')"', "python"),
    ("sleep 30", "sleep"),
])
def test_interrupt_restores_prompt_and_accepts_another_command(
    terminal: tuple[TerminalDispatcher, Path], command: str, process: str,
) -> None:
    dispatcher, directory = terminal
    dispatcher.run(command)
    wait_for(lambda: dispatcher.tmux_command(
        "display-message", "-p", "-t", dispatcher.target, "#{pane_current_command}",
    ).startswith(process))
    assert not dispatcher.ready()

    dispatcher.tmux_command("send-keys", "-t", dispatcher.target, "C-c")

    wait_for(dispatcher.ready)
    dispatcher.run("printf recovered > after-interrupt.txt")
    wait_for(lambda: (directory / "after-interrupt.txt").exists())
    assert (directory / "after-interrupt.txt").read_text() == "recovered"


@pytest.mark.parametrize("typed", ["printf pending", "echo '\n"])
def test_refuses_partial_input_and_continuation_prompts(
    terminal: tuple[TerminalDispatcher, Path], typed: str,
) -> None:
    from terminal import TerminalBusy

    dispatcher, directory = terminal
    dispatcher.tmux_command("send-keys", "-t", dispatcher.target, "-l", typed)
    time.sleep(0.08)
    with pytest.raises(TerminalBusy):
        dispatcher.run("touch unwanted.txt")
    assert not (directory / "unwanted.txt").exists()
    output = dispatcher.tmux_command("capture-pane", "-p", "-t", dispatcher.target)
    assert "touch unwanted" not in output
    assert typed.rstrip() in output


def test_accepts_after_the_learner_clears_unfinished_input(terminal: tuple[TerminalDispatcher, Path]) -> None:
    from terminal import TerminalBusy

    dispatcher, directory = terminal
    dispatcher.tmux_command("send-keys", "-t", dispatcher.target, "-l", "printf unfinished")
    time.sleep(0.08)
    with pytest.raises(TerminalBusy):
        dispatcher.run("touch unwanted.txt")
    dispatcher.tmux_command("send-keys", "-t", dispatcher.target, "C-u")
    time.sleep(0.08)
    dispatcher.run("printf accepted > accepted.txt")
    wait_for(lambda: (directory / "accepted.txt").exists())
    assert (directory / "accepted.txt").read_text() == "accepted"


def test_refuses_input_typed_between_readiness_check_and_delivery(
    terminal: tuple[TerminalDispatcher, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    from terminal import TerminalBusy

    dispatcher, directory = terminal
    tmux_command = dispatcher.tmux_command
    def type_before_delivery(*arguments: str) -> str:
        if arguments[0] == "send-keys":
            tmux_command("send-keys", "-t", dispatcher.target, "-l", "printf learner-input")
        return tmux_command(*arguments)

    monkeypatch.setattr(dispatcher, "tmux_command", type_before_delivery)
    with pytest.raises(TerminalBusy, match="unfinished input"):
        dispatcher.run("touch unwanted.txt")
    assert not (directory / "unwanted.txt").exists()
    output = tmux_command("capture-pane", "-p", "-t", dispatcher.target)
    assert "printf learner-input" in output
    assert "touch unwanted" not in output


@pytest.mark.parametrize("command", ["read -r answer", "bash --noprofile --norc"])
def test_refuses_shell_builtin_read_and_nested_shell(terminal: tuple[TerminalDispatcher, Path], command: str) -> None:
    from terminal import TerminalBusy

    dispatcher, _ = terminal
    dispatcher.run(command)
    wait_for(lambda: not dispatcher.ready())
    with pytest.raises(TerminalBusy):
        dispatcher.run("echo should-not-run")


def test_serializes_concurrent_requests(terminal: tuple[TerminalDispatcher, Path]) -> None:
    from terminal import TerminalBusy

    dispatcher, directory = terminal
    def send(index: int) -> str:
        try:
            dispatcher.run(f"sleep 0.4; echo {index} >> accepted.txt")
            return "sent"
        except TerminalBusy:
            return "busy"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(send, range(2)))
    assert sorted(results) == ["busy", "sent"]
    wait_for(lambda: (directory / "accepted.txt").exists())
    assert len((directory / "accepted.txt").read_text().splitlines()) == 1


def test_preserves_directory_changes_in_the_existing_shell(terminal: tuple[TerminalDispatcher, Path]) -> None:
    dispatcher, directory = terminal
    (directory / "project").mkdir()
    dispatcher.run("cd project")
    wait_for(dispatcher.ready)
    dispatcher.run("printf same-shell > result.txt")
    wait_for(lambda: (directory / "project/result.txt").exists())
    assert (directory / "project/result.txt").read_text() == "same-shell"


def test_refuses_tmux_copy_mode(terminal: tuple[TerminalDispatcher, Path]) -> None:
    from terminal import TerminalBusy

    dispatcher, directory = terminal
    dispatcher.tmux_command("copy-mode", "-t", dispatcher.target)
    with pytest.raises(TerminalBusy):
        dispatcher.run("touch unwanted.txt")
    assert not (directory / "unwanted.txt").exists()


def test_unconfirmed_dispatch_removes_pending_command(
    terminal: tuple[TerminalDispatcher, Path], monkeypatch: pytest.MonkeyPatch,
) -> None:
    from terminal import TerminalUnavailable

    dispatcher, directory = terminal
    tmux_command = dispatcher.tmux_command
    def drop_delivery(*arguments: str) -> str:
        return "" if arguments[0] == "send-keys" else tmux_command(*arguments)

    monkeypatch.setattr(dispatcher, "tmux_command", drop_delivery)
    with pytest.raises(TerminalUnavailable, match="did not confirm"):
        dispatcher.run("touch unwanted.txt")
    assert not (dispatcher.directory / "command").exists()
    # A delayed trigger cannot run a request which has timed out.
    tmux_command("send-keys", "-t", dispatcher.target, "-l", "\x1b[99~")
    time.sleep(0.08)
    assert not (directory / "unwanted.txt").exists()
