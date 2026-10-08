"""Exercise 5: stopping, dispatch, and feedback complete the agent loop.

Run `AGENT_VERBOSE=1 uv run python main.py` after filling the three gaps.
The final evaluation lesson includes the supplied loop tests.
JSON decoding, error-to-text handling, and the step cap are supplied.
The UI in main.py supplies approval wrappers around run_bash and web_fetch.
"""

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
        # Supplied: a bounded loop and a final-step instruction.
        if index == max_iters - 1:
            messages.append({
                "role": "system",
                "content": "This is your last step. Do not call any more tools - "
                           "give your final answer now.",
            })
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=tools)
        msg = response.choices[0].message
        messages.append(msg)

        # EXERCISE 5A: if there are no tool calls, return messages.
        # A final answer ends this turn; it does not prove the task succeeded.
        if not msg.tool_calls:
            return messages

        for call in msg.tool_calls:
            # Supplied: failed decoding or execution becomes matching tool feedback.
            # The model API call above is outside this handler and fails explicitly.
            try:
                args = json.loads(call.function.arguments)
                # EXERCISE 5B: call the named registry function with **args.
                result = registry[call.function.name](**args)
            except Exception as error:
                result = f"Error: {error}"

            # EXERCISE 5C: append role=tool, tool_call_id=call.id, content=result.
            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result,
            })
    return messages
