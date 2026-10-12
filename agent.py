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
    """Send the conversation; return the assistant message."""
    # EXERCISE 1: connect the SDK request.
    # Keep the message object: later it can contain tool calls as well as text.
    raise NotImplementedError("Implement ask in agent.py")


def remember(messages: list[Any], user: str) -> None:
    # EXERCISE 2: currently each question discards the earlier conversation.
    messages[:] = [m for m in messages if isinstance(m, dict) and m.get("role") == "system"]
    messages.append({"role": "user", "content": user})


def run_agent(
    client: Any, messages: list[Any], tool_schemas: list[dict[str, Any]],
    registry: dict[str, Callable[..., str]], max_iters: int = 10,
) -> list[Any]:
    # EXERCISE 3: a single request works for text. Later, handle tool requests.
    messages.append(ask(client, messages, tool_schemas))
    return messages


def read_file(path: str) -> str:
    # EXERCISE 4: discovering a filename does not reveal its contents.
    raise NotImplementedError("Implement read_file in agent.py")


# Tool availability is explicit. Change these lines when the lesson asks.
TOOL_SCHEMAS = []
REGISTRY = {"list_files": list_files, "read_file": read_file}
