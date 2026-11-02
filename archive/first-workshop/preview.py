"""Run the app preview and let a presenter temporarily select the demo app."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from typing import Iterator, TextIO
from urllib.request import urlopen


def selected_project(selection: Path, default: Path) -> Path:
    if selection.is_file():
        selected = json.loads(selection.read_text())
        try:
            os.kill(selected["pid"], 0)
        except ProcessLookupError:
            return default
        return Path(selected["project"])
    return default


@contextmanager
def demo_preview(project: Path) -> Iterator[None]:
    """Select the demo during this session, restoring the learner app on exit."""
    configured = os.environ.get("WORKSHOP_PREVIEW_FILE")
    if not configured:
        log_path = project.parent / "preview.log"
        with log_path.open("w") as log:
            process = start_preview(project, "127.0.0.1", 8000, log)
            try:
                wait_for_preview(process, 8000)
                print("Demo preview: http://127.0.0.1:8000", flush=True)
                yield
            finally:
                stop_preview(process)
        return
    selection = Path(configured)
    temporary = selection.with_suffix(".tmp")
    temporary.write_text(json.dumps({"project": str(project), "pid": os.getpid()}))
    temporary.replace(selection)
    print("App Preview now follows this demo; it returns to your learner app when you exit.", flush=True)
    try:
        yield
    finally:
        selection.unlink(missing_ok=True)


def start_preview(project: Path, host: str, port: int, output: TextIO | None = None) -> subprocess.Popen:
    # Refuse an occupied port rather than showing an unrelated app as the demo.
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            listener.bind((host, port))
        except OSError as error:
            raise RuntimeError(f"Preview port {port} is already in use. Stop that app and retry.") from error
    return subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app:app", "--host", host,
         "--port", str(port), "--reload", "--reload-dir", str(project)],
        cwd=project, start_new_session=True,
        stdout=output or sys.stderr, stderr=output or sys.stderr,
    )


def stop_preview(process: subprocess.Popen) -> None:
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()


def wait_for_preview(process: subprocess.Popen, port: int) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and process.poll() is None:
        try:
            with urlopen(f"http://127.0.0.1:{port}/", timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError("App Preview could not start; inspect preview.log or the runtime logs.")


def serve(selection: Path, default: Path, host: str = "0.0.0.0", port: int = 8000) -> None:
    ready = selection.with_suffix(".ready")

    def publish_ready(project: Path, process: subprocess.Popen) -> None:
        ready.unlink(missing_ok=True)
        wait_for_preview(process, port)
        temporary = ready.with_name(ready.name + ".tmp")
        temporary.write_text(json.dumps({
            "mode": "learner" if project == default else "demo", "revision": str(project),
        }))
        temporary.replace(ready)

    project = selected_project(selection, default)
    process = start_preview(project, host, port)
    try:
        publish_ready(project, process)
        while True:
            time.sleep(0.25)
            target = selected_project(selection, default)
            if target != project:
                stop_preview(process)
                project = target
                process = start_preview(project, host, port)
                publish_ready(project, process)
            if process.poll() is not None:
                raise RuntimeError("App Preview stopped; inspect the runtime logs.")
    finally:
        stop_preview(process)
        ready.unlink(missing_ok=True)


if __name__ == "__main__":
    def stop(_signum: int, _frame: object) -> None:
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, stop)
    try:
        serve(Path(os.environ["WORKSHOP_PREVIEW_FILE"]), Path.cwd() / "capstone")
    except KeyboardInterrupt:
        pass
