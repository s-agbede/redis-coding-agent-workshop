"""Exercise 2: keep conversation history in a Python list.

Run: uv run python -m checkpoints.stage1_chat
Enter prompts to talk to the model. Restarting the process clears the list.
"""

import argparse
from typing import Any

import ui
from first_call import MODEL
from main import build_client
from request_trace import with_request_preview


def chat_turn(client: Any, messages: list[Any], user: str) -> str:
    """Append a user turn, send the history, then retain the assistant reply."""
    messages.append({"role": "user", "content": user})
    response = client.chat.completions.create(model=MODEL, messages=messages)
    message = response.choices[0].message
    messages.append(message)
    return message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--show-messages", action="store_true", help="Preview outgoing messages before each SDK request")
    args = parser.parse_args()
    messages: list[Any] = []
    client = build_client()
    request_client = with_request_preview(client) if args.show_messages else client
    ui.banner(MODEL)
    while True:
        try:
            user = ui.prompt_user().strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user or user.lower() in {"exit", "quit"}:
            break
        answer = chat_turn(request_client, messages, user)
        ui.show_answer(answer)


if __name__ == "__main__":
    main()
