"""The same preview URL follows a demo then returns to the learner app."""
from pathlib import Path
import json
import os
import socket
import subprocess
import sys
import time
from urllib.request import urlopen

import pytest

from preview import demo_preview, start_preview


def wait_for_text(url: str, expected: str) -> None:
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=0.5) as response:
                if expected in response.read().decode():
                    return
        except OSError:
            pass
        time.sleep(0.1)
    raise AssertionError(f"Preview did not show {expected!r}")


def test_preview_switches_actual_apps_and_restores_on_exit_and_interrupt(tmp_path, monkeypatch):
    learner = tmp_path / "learner"
    demo = tmp_path / "demo"
    for project, label in ((learner, "learner app"), (demo, "demo app")):
        project.mkdir()
        (project / "app.py").write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n'
            f'@app.get("/")\ndef home(): return {label!r}\n'
        )
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    selection = tmp_path / "selection"
    monkeypatch.setenv("WORKSHOP_PREVIEW_FILE", str(selection))
    process = subprocess.Popen([
        sys.executable, "-c",
        'from pathlib import Path; from preview import serve; '
        f'serve(Path({str(selection)!r}), Path({str(learner)!r}), "127.0.0.1", {port})',
    ], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}/"
    try:
        wait_for_text(url, "learner app")
        for interrupt in (False, True):
            try:
                with demo_preview(demo):
                    wait_for_text(url, "demo app")
                    if interrupt:
                        raise KeyboardInterrupt
            except KeyboardInterrupt:
                pass
            wait_for_text(url, "learner app")
            assert not selection.exists()
        assert "learner app" in (learner / "app.py").read_text()
    finally:
        process.send_signal(2)
        process.wait(timeout=10)


def test_occupied_preview_port_fails_before_launching_another_server(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        port = listener.getsockname()[1]
        with pytest.raises(RuntimeError, match="already in use"):
            start_preview(tmp_path, "127.0.0.1", port)
