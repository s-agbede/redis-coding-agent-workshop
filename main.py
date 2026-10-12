"""Entry point: wire the model client + tools + pretty-REPL around the agent loop.

Run:  uv run python main.py
Env:  AGENT_API_KEY, AGENT_BASE_URL (optional), AGENT_MODEL (default: gpt-5)
"""

import argparse
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from openai import OpenAI

import ui
from agent import MODEL, TOOL_SCHEMAS, REGISTRY, remember, run_agent
from dotenv import load_dotenv

load_dotenv()

# Interactive tasks can be long; keep the safety cap but higher than the loop's
# tested default of 10. Overridable via env.
MAX_ITERS = int(os.environ.get("AGENT_MAX_ITERS", "25"))

SYSTEM_PROMPT = (
    "You are a helpful coding assistant. Be clear about what you have and haven't verified. "
    "Format code in fenced Markdown blocks with a language label."
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
        return SYSTEM_PROMPT + "\n\nProject instructions:\n" + instructions.read_text(encoding="utf-8")
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
        remember(messages, user)
        try:
            run_agent(client, messages, TOOL_SCHEMAS, REGISTRY, max_iters=MAX_ITERS)
        except NotImplementedError as error:
            ui.info(str(error))
            return

        # The last message is an assistant object (.content) on a normal finish,
        # but a tool-result dict if the loop stopped on the step cap mid-task.
        last_message = messages[-1]
        answer = getattr(last_message, "content", None)
        if getattr(last_message, "tool_calls", None):
            for call in last_message.tool_calls:
                ui.show_tool_request(call.id, call.function.name, call.function.arguments)
            ui.info("Pending tool requests were not executed. Add dispatch and feedback in agent.py; then restart.")
            return
        elif answer:
            ui.show_answer(answer)
        elif isinstance(last_message, dict) and last_message.get("role") == "tool":
            ui.info(
                f"reached the {MAX_ITERS}-step limit before finishing — "
                'type "continue" to keep going (the conversation is kept), '
                "or raise AGENT_MAX_ITERS"
            )
        else:
            ui.info("The model returned no answer text. Try asking again.")


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
