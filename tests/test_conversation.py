"""History is owned by the learner program, not the provider connection."""
from agent import ask, remember
from tests.fakes import FakeClient, text


def test_next_turn_resends_user_and_assistant_history():
    client = FakeClient([text("First code"), text("Revised code")])
    messages = []
    for prompt in ["Write FizzBuzz", "Now stop at 20"]:
        remember(messages, prompt)
        messages.append(ask(client, messages, []))
    assert len(client.calls[0]["messages"]) == 1
    sent = client.calls[1]["messages"]
    assert len(sent) == 3
    assert sent[0]["content"] == "Write FizzBuzz"
    assert sent[1].content == "First code"
    assert sent[2]["content"] == "Now stop at 20"


def test_new_history_does_not_contain_previous_session():
    old = []
    remember(old, "earlier")
    fresh = []
    remember(fresh, "new question")
    assert fresh == [{"role": "user", "content": "new question"}]
