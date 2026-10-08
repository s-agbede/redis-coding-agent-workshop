"""Exercise 1: send one model request with `uv run python first_call.py`.

The OpenAI SDK client handles HTTP requests and responses for the model API.
Our Python code supplies the model name and messages, then reads the reply.
"""

import argparse
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from request_trace import with_request_preview

load_dotenv(dotenv_path=".env")
MODEL = os.environ.get("AGENT_MODEL", "gpt-5")
FIZZBUZZ_PROMPT = (
    "Write a Python function that returns FizzBuzz for the integers 1 to 15. "
    "Use Fizz for multiples of 3, Buzz for multiples of 5, and FizzBuzz for both. "
    "Return only the code."
)


def ask(client: Any, prompt: str) -> str:
    """Send a user message and return the assistant's text."""
    messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content or ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", default=FIZZBUZZ_PROMPT)
    parser.add_argument("--show-messages", action="store_true", help="Preview outgoing messages before each SDK request")
    args = parser.parse_args()
    client = OpenAI(
        api_key=os.environ.get("AGENT_API_KEY"),
        base_url=os.environ.get("AGENT_BASE_URL") or None,
    )
    request_client = with_request_preview(client) if args.show_messages else client
    print(f"PROMPT: {args.prompt}")
    answer = ask(request_client, args.prompt)
    print(f"ASSISTANT: {answer}")


if __name__ == "__main__":
    main()
