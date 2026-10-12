"""The learner's model request, checked without a provider or API key."""
import agent
from tests.fakes import FakeClient, text


def test_ask_sends_the_conversation_and_returns_the_whole_message():
    reply = text("def fizzbuzz(n): ...")
    client = FakeClient([reply])
    messages = [{"role": "user", "content": "Write FizzBuzz in Python."}]
    answer = agent.ask(client, messages, [])
    assert answer.content == "def fizzbuzz(n): ..."
    assert client.calls[0]["model"] == agent.MODEL
    assert client.calls[0]["messages"] == messages
    assert "tools" not in client.calls[0]


def test_ask_preserves_empty_content_and_advertises_supplied_tools():
    client = FakeClient([text(None)])
    assert agent.ask(client, [], [agent.LIST_SCHEMA]).content is None
    assert client.calls[0]["tools"] == [agent.LIST_SCHEMA]
