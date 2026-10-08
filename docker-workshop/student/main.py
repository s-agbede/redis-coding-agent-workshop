"""Entry point: wire the model client + tools + pretty-REPL around the agent loop.

Run:  uv run main.py
Env:  AGENT_API_KEY, AGENT_BASE_URL (optional), AGENT_MODEL (default: gpt-5)
"""

import argparse
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from openai import OpenAI

import ui
from agent import MODEL, run_agent
from tools import GATED, REGISTRY, TOOL_SCHEMAS
from dotenv import load_dotenv

load_dotenv()

# Interactive tasks can be long; keep the safety cap but higher than the loop's
# tested default of 10. Overridable via env.
MAX_ITERS = int(os.environ.get("AGENT_MAX_ITERS", "25"))

SYSTEM_PROMPT = (
    "You are a minimal coding agent. Use the provided tools to accomplish the "
    "user's task, then verify your work with tests, commands, or observable "
    "output. Use list_files and read_file to inspect projects before editing. "
    "Prefer str_replace for edits. When you start a long-running server with "
    "run_bash, redirect stdout and stderr to a log and background it so control returns, "
    "then verify it with a separate command. Bind preview servers to 0.0.0.0:8000. "
    "Ask before creating a new project folder. Finish with these report labels: "
    "Changed files; Commands run; Results; Unverified. Report actual exit codes and "
    "failures. Only call a failure pre-existing when you observed it before editing. "
    "Never claim a denied or unexecuted check passed."
)


def build_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("AGENT_API_KEY"),
        base_url=os.environ.get("AGENT_BASE_URL") or None,
        timeout=float(os.environ.get("AGENT_REQUEST_TIMEOUT", "90")),
    )


def build_system_prompt(project: Path) -> str:
    instructions = project / "AGENTS.md"
    if instructions.is_file():
        return SYSTEM_PROMPT + "\n\nProject instructions (selected workspace):\n" + instructions.read_text(encoding="utf-8")
    return SYSTEM_PROMPT


@contextmanager
def project_directory(project: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(project)
    try:
        yield
    finally:
        os.chdir(previous)


def interactive_session(client: OpenAI, project: Path) -> None:
    client = ui.with_spinner(client)
    approvals = ui.Approvals()
    registry = ui.wrap_registry(REGISTRY, GATED, approvals)
    messages = [{"role": "system", "content": build_system_prompt(project)}]

    ui.banner(MODEL)
    while True:
        try:
            user = ui.prompt_user().strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        low = user.lower()
        if low in {"exit", "quit"}:
            break
        if low == "/auto":
            state = approvals.toggle()
            ui.info(f"auto-approve {'ON' if state else 'OFF'}")
            continue

        messages.append({"role": "user", "content": user})
        run_agent(client, messages, TOOL_SCHEMAS, registry, max_iters=MAX_ITERS)

        # The last message is an assistant object (.content) on a normal finish,
        # but a tool-result dict if the loop stopped on the step cap mid-task.
        answer = getattr(messages[-1], "content", None)
        if answer:
            ui.show_answer(answer)
        else:
            ui.info(
                f"reached the {MAX_ITERS}-step limit before finishing — "
                'type "continue" to keep going (the conversation is kept), '
                "or raise AGENT_MAX_ITERS"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run your coding agent in a selected project.")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Trusted project directory; loads its AGENTS.md if present")
    args = parser.parse_args()
    project = args.project.resolve()
    if not project.is_dir():
        parser.error(f"Project directory does not exist: {project}")
    client = build_client()
    with project_directory(project):
        interactive_session(client, project)


if __name__ == "__main__":
    main()
