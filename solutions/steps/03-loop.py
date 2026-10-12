"""Your evolving coding agent. Start it with: uv run python main.py.

Edit this file throughout the workshop. main.py supplies the terminal session,
client setup and approval UI; tools.py supplies helpers and the other tools.
"""

import json
import os
from collections.abc import Callable
from pathlib import Path
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
) -> list[Any]:
    for _ in range(max_iters):
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


def read_file(path: str) -> str:
    # EXERCISE 4: discovering a filename does not reveal its contents.
    raise NotImplementedError("Implement read_file in agent.py")


# Tool availability is explicit. Change these lines when the lesson asks.
TOOL_SCHEMAS = [LIST_SCHEMA, PLAIN_READ_SCHEMA]
REGISTRY = {"list_files": list_files, "read_file": read_file}
