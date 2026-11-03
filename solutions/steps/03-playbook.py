"""Your Memory workshop agent. Run from the repository root: uv run --group iris python main.py.

Edit this file throughout the workshop. main.py supplies the terminal session,
client setup and approval UI; tools.py supplies helpers and the other tools.
"""

import json
import os
from collections.abc import Callable
from pathlib import Path
from datetime import datetime, timezone
from redis_agent_memory import AgentMemory, models
from context import PublishedSkill
from typing import Any

from dotenv import load_dotenv

import ui
from tools import (
    LIST_SCHEMA, PAGED_READ_SCHEMA, PLAIN_READ_SCHEMA,
    WRITE_FILE_SCHEMA, STR_REPLACE_SCHEMA, RUN_BASH_SCHEMA,
    file_excerpt, list_files, write_file, str_replace, run_bash,
)

load_dotenv(dotenv_path=".env")
MODEL = os.environ.get("AGENT_MODEL", "gpt-5")


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
    registry: dict[str, Callable[..., str]], max_iters: int = 10,
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


# Tool availability is explicit. Change these lines when the lesson asks.
TOOL_SCHEMAS = [LIST_SCHEMA, PAGED_READ_SCHEMA, WRITE_FILE_SCHEMA, STR_REPLACE_SCHEMA, RUN_BASH_SCHEMA]
REGISTRY = {
    "list_files": list_files, "read_file": read_file,
    "write_file": write_file, "str_replace": str_replace, "run_bash": run_bash,
}


# Enable each capability explicitly after implementing its lesson functions.
CAPTURE_ENABLED = True
RECALL_ENABLED = True
PLAYBOOK_ENABLED = True


def record_event(
    memory: AgentMemory, session_id: str, actor_id: str,
    role: models.MessageRole, text: str,
) -> None:
    memory.add_session_event(
        session_id=session_id, actor_id=actor_id, role=role,
        content=[models.Text(text=text)], created_at=datetime.now(timezone.utc),
    )


def recall_preferences(memory: AgentMemory, owner: str, query: str) -> list[dict[str, Any]]:
    response = memory.search_long_term_memory(request={
        "text": query,
        "filter_": {"owner_id": {"eq": owner}, "memory_type": {"eq": "coding_preference"}},
        "limit": 5,
    })
    return response.model_dump(mode="json", by_alias=True)["items"]


def preference_context(items: list[dict[str, Any]]) -> str:
    if not items:
        return ""
    return "What you know about this user's preferences:\n" + "\n".join(f"- {item['text']}" for item in items)


def skill_context(skill: PublishedSkill | None) -> str:
    if skill is None:
        return ""
    return f"Team procedure from Redis Agent Playbook ({skill.name}, version {skill.version}):\n{skill.instructions}"
