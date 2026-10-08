"""Send one command to the existing workshop Bash prompt through its readline hook."""

import fcntl
import os
import subprocess
import time
from pathlib import Path


class TerminalBusy(Exception):
    """The shell cannot accept a new command without disturbing existing input."""


class TerminalUnavailable(Exception):
    """The terminal or its readiness hook is not available."""


class TerminalDispatcher:
    def __init__(
        self,
        directory: Path | None = None,
        target: str = "workshop:0.0",
        tmux: tuple[str, ...] = ("tmux",),
    ) -> None:
        self.directory = directory or Path(os.getenv("WORKSHOP_RUN_DIR", "/tmp/workshop-terminal"))
        self.target = target
        self.tmux = tmux

    def tmux_command(self, *arguments: str) -> str:
        try:
            result = subprocess.run(
                [*self.tmux, *arguments], check=True, capture_output=True,
                text=True, timeout=2,
            )
        except (OSError, subprocess.SubprocessError) as error:
            raise TerminalUnavailable("Terminal is unavailable. Reload the workshop or contact the instructor.") from error
        return result.stdout.rstrip("\n")

    def ready(self) -> bool:
        state = self.tmux_command(
            "display-message", "-p", "-t", self.target,
            "#{pane_current_command}|#{@workshop_ready}|#{pane_in_mode}|#{pane_pid}|#{@workshop_shell_pid}",
        ).split("|")
        return len(state) == 5 and state[:3] == ["bash", "1", "0"] and state[3] == state[4]

    def run(self, command: str) -> None:
        self.directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        # A filesystem lock also serializes separate API worker processes.
        with (self.directory / "dispatch.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise TerminalBusy("Another command is being sent. Check Terminal before trying again.") from error
            try:
                self._send(command)
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _send(self, command: str) -> None:
        if not self.ready():
            raise TerminalBusy("Terminal is busy. Finish or exit its current program, then run the code again.")
        request = self.directory / "command"
        result = self.directory / "result"
        result.unlink(missing_ok=True)
        request.write_text(command, encoding="utf-8")
        try:
            # Only a private readline binding enters the pane. The shell checks
            # its current edit buffer before loading any user-supplied command.
            self.tmux_command("send-keys", "-t", self.target, "-l", "\x1b[99~")
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                if result.exists():
                    status = result.read_text(encoding="utf-8").strip()
                    if status == "sent":
                        return
                    if status == "busy":
                        raise TerminalBusy("Terminal has unfinished input. Finish or clear it before running code.")
                time.sleep(0.01)
            raise TerminalUnavailable("Terminal did not confirm the command. Check Terminal before trying again.")
        finally:
            request.unlink(missing_ok=True)
            result.unlink(missing_ok=True)
