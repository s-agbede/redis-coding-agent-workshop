"""Lesson 4 catch-up: a working loop before lesson 5 adds error feedback."""

import json
import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env")
MODEL = os.environ.get("AGENT_MODEL", "gpt-5")


def run_agent(
    client: Any,
    messages: list[Any],
    tools: list[dict[str, Any]],
    registry: dict[str, Callable[..., str]],
    max_iters: int = 10,
) -> list[Any]:
    for index in range(max_iters):
        if index == max_iters - 1:
            messages.append({
                "role": "system",
                "content": "This is your last step. Do not call any more tools - "
                           "give your final answer now.",
            })
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        message = response.choices[0].message
        messages.append(message)
        if not message.tool_calls:
            return messages
        for call in message.tool_calls:
            args = json.loads(call.function.arguments)
            result = registry[call.function.name](**args)
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })
    return messages
