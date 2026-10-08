"""Exercise 2: the caller owns history; every request includes it explicitly."""

from typing import Any

from checkpoints import stage1_chat
from tests.fakes import FakeClient, text


def test_next_turn_resends_user_and_assistant_history() -> None:
    assert hasattr(stage1_chat, "chat_turn"), "Implement chat_turn in stage1_chat.py"
    client = FakeClient([text("Use multiples of three and five."), text("Both means FizzBuzz.")])
    messages: list[Any] = []

    first = stage1_chat.chat_turn(client, messages, "Explain FizzBuzz.")
    second = stage1_chat.chat_turn(client, messages, "What about both?")

    assert first == "Use multiples of three and five."
    assert second == "Both means FizzBuzz."
    assert len(client.calls[0]["messages"]) == 1
    sent = client.calls[1]["messages"]
    assert len(sent) == 3
    assert sent[0] == {"role": "user", "content": "Explain FizzBuzz."}
    assert sent[1].role == "assistant" and sent[1].content == first
    assert sent[2] == {"role": "user", "content": "What about both?"}
    assert len(messages) == 4


def test_new_history_does_not_contain_previous_session() -> None:
    assert hasattr(stage1_chat, "chat_turn"), "Implement chat_turn in stage1_chat.py"
    client = FakeClient([text("Understood."), text("Which problem?")])
    stage1_chat.chat_turn(client, [], "We are implementing FizzBuzz.")
    fresh: list[Any] = []

    answer = stage1_chat.chat_turn(client, fresh, "What are we implementing?")

    assert answer == "Which problem?"
    assert client.calls[1]["messages"] == [
        {"role": "user", "content": "What are we implementing?"},
    ]


def test_fake_records_request_at_send_time() -> None:
    messages = [{"role": "user", "content": "first"}]
    client = FakeClient([text("reply")])
    client.chat.completions.create(model="test", messages=messages)
    messages[0]["content"] = "changed"
    messages.append({"role": "user", "content": "later"})
    assert client.calls[0]["messages"] == [{"role": "user", "content": "first"}]
