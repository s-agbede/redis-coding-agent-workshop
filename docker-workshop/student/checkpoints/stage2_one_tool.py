"""Inspect a single request/execution/result round trip before building a loop.

Run: uv run python -m checkpoints.stage2_one_tool
The harness pauses before executing each read requested by the model.
"""

import argparse
import json
from collections.abc import Callable
from typing import Any

from main import build_client
from agent import MODEL
from tools import TOOL_SCHEMAS, read_file

FILE_QUESTION = "Read checkpoints/project_brief.md. What is this project's release name?"

PLAIN_READ_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the complete UTF-8 contents of a known local file.",
        "parameters": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
}


def round_trip(
    client: Any,
    prompt: str,
    reader: Callable[..., str] = read_file,
    pause: Callable[[str], str] | None = None,
    *,
    paged: bool = False,
) -> list[Any]:
    """Two model calls, with Python executing read requests between them."""
    schemas = ([tool for tool in TOOL_SCHEMAS if tool["function"]["name"] == "read_file"]
               if paged else [PLAIN_READ_SCHEMA])
    messages: list[Any] = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=schemas)
    request = response.choices[0].message
    messages.append(request)
    if not request.tool_calls:
        print("The model answered without a read. Try explicitly asking it to use read_file.")
        return messages
    for call in request.tool_calls:
        print(f"REQUEST {call.id}: {call.function.name}({call.function.arguments})")
        if pause:
            pause("Nothing has executed yet. Predict the result; press Enter to run Python. ")
        print(f"HARNESS: Python is now executing {call.function.name}.")
        try:
            if call.function.name != "read_file":
                raise ValueError("This checkpoint only permits read_file")
            result = reader(**json.loads(call.function.arguments))
        except Exception as error:
            result = f"Error: {error}"
        print(f"RESULT {call.id} ({len(result)} characters, not tokens):\n{result}")
        messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    print("HARNESS: sending the assistant request and matching tool result back.")
    response = client.chat.completions.create(model=MODEL, messages=messages, tools=schemas)
    reply = response.choices[0].message
    messages.append(reply)
    for call in reply.tool_calls or []:
        print(f"REQUEST {call.id}: {call.function.name}({call.function.arguments}) "
              "(not executed: this checkpoint stops after one exchange)")
    return messages


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default=FILE_QUESTION, help="Question to send to the model")
    parser.add_argument("--paged", action="store_true", help="Use the improved reader schema after lesson 5")
    args = parser.parse_args()
    print(f"PROMPT: {args.prompt}")
    client = build_client()
    messages = round_trip(client, args.prompt, pause=input, paged=args.paged)
    print(f"ANSWER: {messages[-1].content or 'Another tool was requested; the next lesson adds the loop.'}")


if __name__ == "__main__":
    main()
