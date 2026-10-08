"""Independent HTTP acceptance checks for the task-board repair exercise.

Run `python verify_capstone.py --project capstone`, or use `--url` for an existing
preview. Each check creates its own task and deletes only that task afterwards.
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from pydantic import BaseModel, ConfigDict


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool
    detail: str


class TaskRecord(BaseModel):
    model_config = ConfigDict(strict=True)
    id: str
    title: str
    completed: bool


def request(url: str, method: str = "GET", body: object = None) -> tuple[int, str]:
    data = json.dumps(body).encode() if body is not None else None
    req = Request(url, data=data, method=method,
                  headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=3) as response:
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        return error.code, error.read().decode("utf-8", errors="replace")


def require(condition: bool, detail: str) -> None:
    if not condition:
        raise AssertionError(detail)


def verify_url(url: str) -> list[Check]:
    """Check observable behaviour, preserving all tasks that existed beforehand."""
    url = url.rstrip("/")
    checks: list[Check] = []

    def check(name: str, action: Callable[[], str]) -> bool:
        try:
            detail = action()
        except Exception as error:
            checks.append(Check(name, False, str(error)))
            return False
        checks.append(Check(name, True, detail))
        return True

    def homepage() -> str:
        status, body = request(url + "/")
        require(status == 200, f"GET / returned {status}; expected 200")
        require("<html" in body.lower() and "<form" in body.lower(),
                "GET / must serve the task-board HTML page")
        return "GET / serves the task-board page"

    check("homepage", homepage)
    title = f"Acceptance check {uuid4().hex[:10]}"
    task_id = ""
    task_url = ""

    def create() -> str:
        nonlocal task_id, task_url
        status, body = request(url + "/tasks", "POST", {"title": title})
        payload = json.loads(body)
        returned_id = payload.get("id") if isinstance(payload, dict) else None
        # Keep the cleanup target even when another field fails validation.
        if isinstance(returned_id, str) and returned_id.strip():
            task_id = returned_id
            task_url = f"{url}/tasks/{quote(task_id, safe='')}"
        require(status == 201, f"POST /tasks returned {status}; expected 201")
        created = TaskRecord.model_validate(payload)
        require(bool(created.id), "Created task needs an ID")
        require(created.title == title and created.completed is False,
                "New task must preserve its title and start incomplete")
        return "POST /tasks creates an incomplete task (201)"

    def read(expected: bool) -> str:
        status, body = request(task_url)
        require(status == 200, f"GET task returned {status}; expected 200")
        task = TaskRecord.model_validate_json(body)
        expected_text = str(expected).lower()
        require(task.id == task_id and task.title == title,
                "GET task changed its identity or title")
        require(task.completed is expected,
                f"GET task expected completed={expected_text}; got completed={str(task.completed).lower()}")
        status, body = request(url + "/tasks")
        require(status == 200, f"GET /tasks returned {status}; expected 200")
        entries = json.loads(body)
        require(isinstance(entries, list), "GET /tasks must return a list")
        matching = [TaskRecord.model_validate(item) for item in entries
                    if isinstance(item, dict) and item.get("id") == task_id]
        require(len(matching) == 1, "GET /tasks must include the created task exactly once")
        require(matching[0] == task, "GET /tasks and GET task disagree")
        return f"GET task and GET /tasks retain completed={expected_text}"

    def update(completed: bool) -> str:
        status, body = request(task_url, "PATCH", {"completed": completed})
        require(status == 200, f"PATCH task returned {status}; expected 200")
        task = TaskRecord.model_validate_json(body)
        require(task.id == task_id and task.title == title and task.completed is completed,
                "PATCH must return the same task with the requested completion value")
        return f"PATCH returns completed={str(completed).lower()}"

    def unknown() -> str:
        missing = f"{url}/tasks/missing-{uuid4().hex}"
        for method in ("GET", "PATCH", "DELETE"):
            status, _ = request(missing, method,
                                {"completed": True} if method == "PATCH" else None)
            require(status == 404, f"{method} unknown task returned {status}; expected 404")
        return "GET, PATCH, and DELETE unknown task return 404"

    def cleanup() -> str:
        status, _ = request(task_url, "DELETE")
        require(status == 204, f"DELETE own test task returned {status}; expected 204")
        status, _ = request(task_url)
        require(status == 404, "Deleted test task is still readable")
        return "Removed only the task created by this check"

    try:
        if not check("create", create):
            return checks
        check("read", lambda: read(False))
        check("complete response", lambda: update(True))
        check("complete persistence", lambda: read(True))
        check("uncomplete response", lambda: update(False))
        check("uncomplete persistence", lambda: read(False))
        check("unknown ID", unknown)
    finally:
        if task_id:
            check("cleanup", cleanup)
    return checks


@contextmanager
def running_app(project: Path) -> Iterator[str]:
    """Run one isolated Uvicorn process on a reserved ephemeral loopback port."""
    project = Path(project).resolve()
    if not (project / "app.py").is_file():
        raise RuntimeError(f"No app.py found in {project}")
    with socket.socket() as listener, tempfile.TemporaryFile(mode="w+") as log:
        listener.bind(("127.0.0.1", 0))
        listener.listen(128)
        port = listener.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app:app", "--fd", str(listener.fileno()),
             "--log-level", "warning"],
            cwd=project, stdout=log, stderr=log, pass_fds=(listener.fileno(),),
        )
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if proc.poll() is not None:
                    break
                try:
                    with urlopen(url + "/openapi.json", timeout=0.2) as response:
                        if response.status == 200:
                            break
                except (URLError, OSError):
                    time.sleep(0.05)
            else:
                raise RuntimeError("Test server did not become ready within 10 seconds")
            if proc.poll() is not None:
                log.seek(0)
                raise RuntimeError("Test server exited: " + log.read()[-1500:].strip())
            yield url
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)


def verify_project(project: Path) -> list[Check]:
    try:
        with running_app(project) as url:
            return verify_url(url)
    except (OSError, RuntimeError) as error:
        return [Check("server startup", False, str(error))]


def print_results(checks: Sequence[Check]) -> None:
    for check in checks:
        print(f"{'PASS' if check.passed else 'FAIL'} {check.name}: {check.detail}")
    passed = sum(check.passed for check in checks)
    print(f"{passed}/{len(checks)} acceptance checks passed")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group()
    target.add_argument("--project", type=Path, default=Path("capstone"))
    target.add_argument("--url", help="Check a running preview without restarting it")
    args = parser.parse_args(argv)
    checks = verify_url(args.url) if args.url else verify_project(args.project)
    print_results(checks)
    return 0 if checks and all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
