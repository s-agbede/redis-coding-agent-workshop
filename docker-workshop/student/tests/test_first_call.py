"""Exercise 1: one SDK call, checked without a provider or API key."""

import first_call
from tests.fakes import FakeClient, text


def test_ask_sends_the_prompt_and_returns_the_assistant_text() -> None:
    assert hasattr(first_call, "ask"), "Implement ask(client, prompt) in first_call.py"
    client = FakeClient([text("def fizzbuzz(n): ...")])

    answer = first_call.ask(client, "Write FizzBuzz in Python.")

    assert answer == "def fizzbuzz(n): ..."
    assert len(client.calls) == 1
    assert client.calls[0]["model"] == first_call.MODEL
    assert client.calls[0]["messages"] == [
        {"role": "user", "content": "Write FizzBuzz in Python."},
    ]
    assert "tools" not in client.calls[0]


def test_ask_does_not_invent_text_for_an_empty_response() -> None:
    assert hasattr(first_call, "ask"), "Implement ask(client, prompt) in first_call.py"
    assert first_call.ask(FakeClient([text(None)]), "Hello") == ""
