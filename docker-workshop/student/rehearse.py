"""Run the task-board repair N times against the real model.

Usage: uv run python rehearse.py -n 5
Env: AGENT_API_KEY, optional AGENT_BASE_URL / AGENT_MODEL / AGENT_REQUEST_TIMEOUT / AGENT_MAX_ITERS

Each run copies the broken fixture into a temporary directory, gives the completed
agent its real tools, then independently checks the app over HTTP. Shell tools run
headlessly here; this is a facilitator reliability check, not a learner sandbox.
The source capstone must be a clean starter: only completion persistence may fail.
An already repaired or otherwise invalid baseline stops before the model is called.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import os
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from openai import OpenAI

from main import MAX_ITERS
from solutions.agent import MODEL, run_agent
from solutions.tools import MAX_OUTPUT_CHARS, REGISTRY, TOOL_SCHEMAS
from verify_capstone import Check, print_results, verify_project

ROOT = Path(__file__).resolve().parent
SYSTEM = (
    "You are a coding agent repairing an existing application. Read AGENTS.md, "
    "reproduce the failure, make the smallest coherent fix, and verify your work. "
    "Do not start a long-running preview server: the acceptance command starts "
    "and stops its own test server. Your final answer must list files changed, "
    "commands run, observed results, and anything not verified."
)
CAPSTONE = (
    "Repair this task board. Checking a task appears to complete it, but a page "
    "refresh makes it incomplete again. Preserve the existing page and API. "
    "Do not modify the acceptance verifier, its checks, or any workshop tests. "
    "In this temporary copy, replace the relative verifier command in AGENTS.md "
    "with this absolute command (do not edit AGENTS.md):\n\n"
    "```bash\n{command}\n```\n\n"
    "Run it before and after the repair, and fix the application code until all "
    "checks pass. Tasks may reset when the server process restarts."
)


def build_client() -> OpenAI:
    load_dotenv(dotenv_path=".env", override=True)
    try:
        timeout = float(os.environ.get("AGENT_REQUEST_TIMEOUT", "90"))
    except ValueError as error:
        raise ValueError("AGENT_REQUEST_TIMEOUT must be a number of seconds") from error
    if not math.isfinite(timeout) or not 0 < timeout <= 300:
        raise ValueError("AGENT_REQUEST_TIMEOUT must be greater than 0 and at most 300 seconds")
    return OpenAI(
        api_key=os.environ.get("AGENT_API_KEY"),
        base_url=os.environ.get("AGENT_BASE_URL") or None,
        timeout=timeout,
    )


def stop_command(proc: subprocess.Popen[str]) -> None:
    """Stop a shell's process group, including any background children it left."""
    try:
        os.killpg(proc.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        proc.wait(timeout=1)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    proc.wait(timeout=3)


@contextmanager
def rehearsal_tools() -> Iterator[dict[str, Callable[..., str]]]:
    processes: list[subprocess.Popen[str]] = []

    def run_bash(command: str, timeout: float = 60) -> str:
        if not math.isfinite(timeout) or not 0 < timeout <= 60:
            raise ValueError("Shell timeout must be greater than 0 and at most 60 seconds")
        proc = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True,
        )
        processes.append(proc)
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            stop_command(proc)
            stdout, stderr = proc.communicate(timeout=3)
            status = f"timeout\nCommand timed out after {timeout:g}s"
        else:
            status = str(proc.returncode)
        out = stdout + stderr
        if len(out) > MAX_OUTPUT_CHARS:
            out = out[-MAX_OUTPUT_CHARS:] + (
                f"\n... [truncated; showing last {MAX_OUTPUT_CHARS} of {len(out)} characters; "
                "narrow the command for more detail]"
            )
        return f"exit {status}\n{out}".strip()

    try:
        yield {**REGISTRY, "run_bash": run_bash}
    finally:
        for proc in processes:
            stop_command(proc)


def message_record(message: Any) -> dict[str, Any]:
    """Keep the visible conversation, without client configuration or headers."""
    if isinstance(message, dict):
        return message
    return {
        "role": "assistant",
        "content": message.content,
        "tool_calls": [
            {"id": call.id, "type": "function", "function": {
                "name": call.function.name, "arguments": call.function.arguments,
            }}
            for call in message.tool_calls or []
        ],
    }


def save_evidence(
    artifacts: Path, workdir: Path, before: dict[str, str], messages: list[Any],
    baseline: list[Check], checks: list[Check], outcome: str, error: str | None,
    responses: list[dict[str, Any]],
) -> None:
    records = [message_record(message) for message in messages]
    turns = sum(record.get("role") == "assistant" for record in records)
    last_role = records[-1].get("role") if records else None
    stop_reason = (
        "error" if error else "not_started" if not turns else
        "iteration_limit" if last_role == "tool" else "final_answer"
    )
    artifacts.mkdir(parents=True, exist_ok=False, mode=0o700)
    report = {
        "model": MODEL, "outcome": outcome, "stop_reason": stop_reason,
        "model_turns": turns, "error": error,
        "model_responses": responses,
        "baseline_checks": [asdict(check) for check in baseline],
        "final_checks": [asdict(check) for check in checks], "messages": records,
    }
    (artifacts / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    changes = []
    for name, original in before.items():
        path = workdir / name
        current = path.read_text(encoding="utf-8") if path.is_file() else ""
        changes.extend(difflib.unified_diff(
            original.splitlines(keepends=True), current.splitlines(keepends=True),
            fromfile=f"before/{name}", tofile=f"after/{name}",
        ))
    (artifacts / "changes.diff").write_text("".join(changes), encoding="utf-8")
    print(f"Trace: {artifacts} ({turns} model turns; {stop_reason})", flush=True)


def one_run(client: OpenAI, *, artifacts: Path | None = None) -> bool:
    original_cwd = Path.cwd()
    artifacts = artifacts.resolve() if artifacts is not None else None
    with tempfile.TemporaryDirectory(prefix="capstone-") as directory:
        workdir = Path(directory) / "capstone"
        shutil.copytree(ROOT / "capstone", workdir,
                        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        before = {path.name: path.read_text(encoding="utf-8") for path in workdir.iterdir()
                  if path.is_file() and path.suffix in {".py", ".html", ".md"}}
        baseline: list[Check] = []
        checks: list[Check] = []
        messages: list[Any] = []
        responses: list[dict[str, Any]] = []
        outcome = "invalid_baseline"
        error: str | None = None
        command = shlex.join([sys.executable, str(ROOT / "verify_capstone.py"), "--project", "."])

        def create(**kwargs: Any) -> Any:
            response = client.chat.completions.create(**kwargs)
            usage = getattr(response, "usage", None)
            responses.append({
                "model": getattr(response, "model", kwargs["model"]),
                "finish_reason": getattr(response.choices[0], "finish_reason", None),
                "usage": usage.model_dump() if usage is not None else None,
            })
            return response

        traced_client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        try:
            baseline = verify_project(workdir)
            if [check.name for check in baseline if not check.passed] != ["complete persistence"]:
                print("Baseline invalid: use a clean starter whose only failing check is "
                      "complete persistence. Restore the original capstone source before rehearsing.")
                print_results(baseline)
                return False
            print("Baseline confirmed: the expected completion-persistence defect is present.", flush=True)
            try:
                os.chdir(workdir)
                messages = [
                    {"role": "system", "content": SYSTEM},
                    {"role": "user", "content": CAPSTONE.format(command=command)},
                ]
                with rehearsal_tools() as registry:
                    run_agent(traced_client, messages, TOOL_SCHEMAS, registry, max_iters=MAX_ITERS)
            except Exception as exc:
                error = str(exc)
                outcome = "agent_error"
                print(f"   (run raised: {error})")
                return False
            finally:
                os.chdir(original_cwd)
            checks = verify_project(workdir)
            print_results(checks)
            passed = bool(checks) and all(check.passed for check in checks)
            outcome = "passed" if passed else "failed"
            return passed
        finally:
            if artifacts is not None:
                save_evidence(artifacts, workdir, before, messages, baseline, checks, outcome, error, responses)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=5, help="number of rehearsal runs (default: 5)")
    parser.add_argument("--output-dir", type=Path, default=Path("output/rehearsal"),
                        help="save conversation, checks and source diff in a new subdirectory per run")
    args = parser.parse_args(argv)
    if args.n < 1:
        parser.error("-n must be at least 1")
    client = build_client()
    passes = 0
    for index in range(args.n):
        print(f"run {index + 1}/{args.n}: starting...", flush=True)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
        passed = one_run(client, artifacts=args.output_dir / run_id)
        passes += passed
        print(f"run {index + 1}/{args.n}: {'PASS' if passed else 'FAIL'}  ({passes}/{index + 1})")
    failures = args.n - passes
    print(f"\nCapstone pass rate: {passes}/{args.n} = {100 * passes / args.n:.0f}% "
          f"({passes} passed, {failures} failed)")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
