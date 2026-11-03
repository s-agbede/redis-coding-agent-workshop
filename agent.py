"""Your coding agent. Run from the repository root: uv run --group iris python main.py

Part 1 built the loop: the model asks for a tool, Python runs it, the result goes back.
Part 2 decides what the agent knows. `handle` below does one task from start to finish;
each workshop section switches on one flag and you read the lines it turns on.
"""

import json
import os
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from redis_agent_memory import models

import ui
from tools import (
    LIST_SCHEMA, PAGED_READ_SCHEMA,
    WRITE_FILE_SCHEMA, STR_REPLACE_SCHEMA, RUN_BASH_SCHEMA,
    file_excerpt, list_files, write_file, str_replace, run_bash,
)

load_dotenv(dotenv_path=".env")
MODEL = os.environ.get("AGENT_MODEL", "gpt-5")


# ---------------------------------------------------------------- Part 1: the agent loop

def ask(client: Any, messages: list[Any], tool_schemas: list[dict[str, Any]]) -> Any:
    # An empty schema list is omitted: the first lesson is a text-only request.
    options = {"tools": tool_schemas} if tool_schemas else {}
    ui.show_request(messages)
    with ui.console.status("Thinking…", spinner="dots"):
        response = client.chat.completions.create(
            model=MODEL, messages=messages, **options,
        )
    return response.choices[0].message


def remember(messages: list[Any], user: str) -> None:
    messages.append({"role": "user", "content": user})


def run_agent(
    client: Any, messages: list[Any], tool_schemas: list[dict[str, Any]],
    registry: dict[str, Callable[..., str]], max_iters: int = 25,
    on_request: Callable[[list[Any]], None] | None = None,
) -> list[Any]:
    for _ in range(max_iters):
        if on_request is not None:
            on_request(messages)
        assistant_message = ask(client, messages, tool_schemas)
        messages.append(assistant_message)
        if not assistant_message.tool_calls:
            return messages
        for call in assistant_message.tool_calls:
            ui.show_tool_request(call.id, call.function.name, call.function.arguments)
            try:
                tool_arguments = json.loads(call.function.arguments)
                if call.function.name == "run_bash" and not ui.approve_command(tool_arguments["command"]):
                    result = "User declined to run this tool."
                else:
                    result = registry[call.function.name](**tool_arguments)
            except Exception as error:
                result = f"Error: {error}"
            ui.show_tool_result(call.id, result)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return messages


def read_file(path: str, offset: int = 1, limit: int = 80) -> str:
    text = Path(path).read_text(encoding="utf-8")
    return file_excerpt(text, offset=offset, limit=limit)


TOOL_SCHEMAS = [LIST_SCHEMA, PAGED_READ_SCHEMA, WRITE_FILE_SCHEMA, STR_REPLACE_SCHEMA, RUN_BASH_SCHEMA]
REGISTRY = {
    "list_files": list_files, "read_file": read_file,
    "write_file": write_file, "str_replace": str_replace, "run_bash": run_bash,
}


# ---------------------------------------------------------------- Part 2: what the agent knows

# Each section switches one of these on. Save, type exit, and start the agent again.
CAPTURE = False   # Section 3: Redis Agent Memory records the conversation
RECALL = False    # Section 4: bring back what it learned about you
PLAYBOOK = False  # Section 5: the team's procedure and approved answers from Redis Agent Playbook

SYSTEM = (
    "You are a coding assistant working in this project. Use your tools when a task needs the project's files. "
    "Answer in Markdown, with code in fenced blocks tagged with its language."
)
# Playbook search always returns its closest entries; only use ones clearly about this task.
SKILL_MIN_SCORE = 0.7
FAQ_MIN_SCORE = 0.75


def handle(task: str, session: Any, services: Any) -> str | None:
    """One task, start to finish: what is remembered, what is sent, and what is kept."""

    # Section 3: record what you said, in this session.
    if CAPTURE:
        services.memory.add_session_event(
            session_id=session.session_id, actor_id=session.owner, role=models.MessageRole.USER,
            content=[models.Text(text=task)], created_at=datetime.now(timezone.utc),
        )

    # Section 4: search what Agent Memory learned about you, using the task as the query.
    preferences: list[str] = []
    if RECALL:
        found = services.memory.search_long_term_memory(request={
            "text": task,
            "filter_": {"owner_id": {"eq": session.owner}, "memory_type": {"eq": "coding_preference"}},
            "limit": 5,
        })
        preferences = [item.text for item in found.items]
        ui.info("Recalled: " + ("; ".join(preferences) or "nothing"))

    # Section 5: the team's procedure and approved answers, but only what is relevant to this task.
    skill = None
    answers = []
    if PLAYBOOK:
        skill = services.playbook.retrieve(task, min_score=SKILL_MIN_SCORE)
        ui.info(f"Team procedure: {skill.name}, version {skill.version}" if skill else "Team procedure: none for this task")
        answers = services.playbook.answers(task, min_score=FAQ_MIN_SCORE)
        if answers:
            ui.info("Team answer: " + "; ".join(a.question for a in answers))

    # Build the request: instructions, what was recalled, the conversation so far, then the task.
    messages: list[Any] = [{"role": "system", "content": SYSTEM + "\n\nProject instructions (AGENTS.md):\n" + session.instructions}]
    recalled = []
    if preferences:
        recalled.append("What you know about this user's preferences:\n" + "\n".join(f"- {p}" for p in preferences))
    if skill:
        recalled.append(f"Team procedure from Redis Agent Playbook ({skill.name}, version {skill.version}):\n{skill.instructions}")
    if answers:
        recalled.append("Approved team answers from Redis Agent Playbook:\n" + "\n".join(f"- Q: {a.question}\n  A: {a.answer}" for a in answers))
    if recalled:
        messages.append({"role": "system", "content": "\n\n".join(recalled)})
    conversation_starts = len(messages)
    messages += session.history + [{"role": "user", "content": task}]

    # Part 1's loop does the work. The session keeps the conversation, not the recalled context,
    # so recall runs fresh for every task.
    try:
        run_agent(services.client, messages, TOOL_SCHEMAS, services.tools, on_request=services.on_request)
    finally:
        session.history = messages[conversation_starts:]
    answer = getattr(messages[-1], "content", None)

    # Section 3 again: record the agent's answer too.
    if CAPTURE and answer:
        services.memory.add_session_event(
            session_id=session.session_id, actor_id="coding-assistant", role=models.MessageRole.ASSISTANT,
            content=[models.Text(text=answer)], created_at=datetime.now(timezone.utc),
        )
    return answer
