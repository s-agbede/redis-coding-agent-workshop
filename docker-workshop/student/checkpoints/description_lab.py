"""Compare tool proposals without executing them. Run as a module from project root."""

import argparse
from copy import deepcopy
from typing import Any

from agent import MODEL
from main import build_client
from tools import TOOL_SCHEMAS


def compare_descriptions(client: Any, prompt: str) -> list[dict[str, Any]]:
    proposals = []
    for label in ("vague", "specific"):
        schemas = deepcopy([tool for tool in TOOL_SCHEMAS if tool["function"]["name"] in {"read_file", "run_bash"}])
        if label == "vague":
            schemas[0]["function"]["description"] = "Get some information."
        response = client.chat.completions.create(
            model=MODEL, messages=[{"role": "user", "content": prompt}], tools=schemas,
        )
        message = response.choices[0].message
        names = [call.function.name for call in message.tool_calls or []]
        proposals.append({"description": label, "tools": names})
        print(f"{label.upper()} description: {', '.join(names) or 'text answer; no tool proposed'}")
        for call in message.tool_calls or []:
            print(f"  proposed {call.function.name}({call.function.arguments}) — NOT EXECUTED")
    return proposals


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    if args.offline:
        from tests.fakes import FakeClient, tool_turn

        print("OFFLINE: illustrative scripted proposals, not measured model behavior.")
        client = FakeClient([
            tool_turn(("weak", "run_bash", {"command": "cat checkpoints/notes.txt"})),
            tool_turn(("clear", "read_file", {"path": "checkpoints/notes.txt"})),
        ])
    else:
        client = build_client()
    compare_descriptions(client, "Read checkpoints/notes.txt and tell me what it says.")
    print("Record both choices. Identical routing is a valid observation; descriptions do not guarantee behavior.")


if __name__ == "__main__":
    main()
