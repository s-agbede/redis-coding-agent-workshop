"""Lesson 1: compare request contents without an API key or a model call."""

import argparse
from typing import Literal

from pydantic import BaseModel


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class HistoryRequest(BaseModel):
    label: str
    messages: list[Message]


def history_requests() -> list[HistoryRequest]:
    """Return independent snapshots of the messages our program would send."""
    name = Message(role="user", content="My fictional project is called Cedar.")
    reply = Message(role="assistant", content="Your project is called Cedar.")
    question = Message(role="user", content="What is my project's name?")
    return [
        HistoryRequest(label="FIRST REQUEST", messages=[name.model_copy()]),
        HistoryRequest(
            label="SECOND REQUEST",
            messages=[name.model_copy(), reply.model_copy(), question.model_copy()],
        ),
        HistoryRequest(label="AFTER RESTART", messages=[question.model_copy()]),
    ]


def question_request(remember: bool) -> HistoryRequest:
    """Ask the same question with either retained messages or just this turn."""
    _, retained, latest = history_requests()
    return retained if remember else latest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("latest", "retained", "all"), default="all")
    args = parser.parse_args()
    print("OFFLINE: these are request examples with one prepared assistant reply.")
    print("No request is sent to a model. Predict what each request contains.\n")
    if args.mode != "all":
        request = question_request(remember=args.mode == "retained")
        print("SAME QUESTION: What is my project's name?")
        print(request.model_dump_json(indent=2, exclude={"label"}))
        has_name = any("Cedar" in message.content for message in request.messages)
        print(f"PROJECT NAME IN REQUEST: {'present' if has_name else 'missing'}")
        print("This checks the information we send, not whether a model answers correctly.")
        return
    for request in history_requests():
        print(request.label)
        print(request.model_dump_json(indent=2, exclude={"label"}))
        print()
    print("The second request includes the old messages because Python kept them.")
    print("After restart, only the new question remains. The name is not sent.")
    print("Practice: add a second project detail. Which messages would you send next?")


if __name__ == "__main__":
    main()
