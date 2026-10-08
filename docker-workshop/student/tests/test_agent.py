from agent import run_agent
from tests.fakes import FakeClient, text, tool_turn


def tool_messages(messages):
    return [m for m in messages if isinstance(m, dict) and m.get("role") == "tool"]


def test_records_reply_and_stops_when_model_requests_no_tools():
    # Behavior 1 (tracer bullet): a plain answer with no tool calls ends the loop.
    client = FakeClient([text("hello there")])
    messages = [{"role": "user", "content": "hi"}]

    result = run_agent(client, messages, tools=[], registry={})

    # The assistant's reply is recorded in the conversation...
    assert result[-1].content == "hello there"
    # ...and the model was consulted exactly once (loop terminated immediately).
    assert len(client.calls) == 1


def test_executes_requested_tool_and_appends_result():
    # Behavior 2: a tool call is run and its result fed back as a role:"tool" message.
    seen = {}

    def read_file(path):
        seen["path"] = path
        return "file contents"

    client = FakeClient([
        tool_turn(("call_1", "read_file", {"path": "foo.py"})),
        text("done"),
    ])
    messages = [{"role": "user", "content": "read foo.py"}]

    result = run_agent(client, messages, tools=[], registry={"read_file": read_file})

    # The tool ran with the parsed arguments.
    assert seen["path"] == "foo.py"
    # Exactly one tool-result message, tied to the originating call id, carrying the output.
    results = tool_messages(result)
    assert len(results) == 1
    assert results[0]["tool_call_id"] == "call_1"
    assert results[0]["content"] == "file contents"


def test_loops_across_multiple_tool_rounds_until_model_stops():
    # Behavior 3: the loop keeps consulting the model after each round until it stops asking.
    def noop(**kwargs):
        return "ok"

    client = FakeClient([
        tool_turn(("c1", "noop", {})),
        tool_turn(("c2", "noop", {})),
        text("all done"),
    ])
    messages = [{"role": "user", "content": "go"}]

    result = run_agent(client, messages, tools=[], registry={"noop": noop})

    assert len(client.calls) == 3  # two tool rounds + the final answer
    assert result[-1].content == "all done"


def test_stops_at_iteration_cap_when_model_never_finishes():
    # Behavior 4 (safety): a model that never stops requesting tools cannot spin forever.
    def noop(**kwargs):
        return "ok"

    client = FakeClient([tool_turn((f"c{i}", "noop", {})) for i in range(3)])
    messages = [{"role": "user", "content": "go"}]

    run_agent(client, messages, tools=[], registry={"noop": noop}, max_iters=3)

    assert len(client.calls) == 3  # bounded by max_iters, did not exceed


def test_runs_all_tool_calls_in_a_single_turn_before_next_model_call():
    # Behavior 5: several tool calls in one assistant turn are all run and all fed back.
    order = []

    def rec(name):
        order.append(name)
        return "ok"

    client = FakeClient([
        tool_turn(("a", "rec", {"name": "first"}), ("b", "rec", {"name": "second"})),
        text("done"),
    ])
    messages = [{"role": "user", "content": "go"}]

    result = run_agent(client, messages, tools=[], registry={"rec": rec})

    assert order == ["first", "second"]
    assert [r["tool_call_id"] for r in tool_messages(result)] == ["a", "b"]
    assert len(client.calls) == 2  # both results appended before consulting the model again


def test_dispatches_to_the_named_tool_with_parsed_args():
    # Behavior 6: dispatch routes to the correct tool by name and passes parsed arguments.
    def adder(x, y):
        return str(x + y)

    def shouter(text):
        return text.upper()

    client = FakeClient([
        tool_turn(("c1", "shouter", {"text": "hi"})),
        text("done"),
    ])
    messages = [{"role": "user", "content": "go"}]

    result = run_agent(
        client, messages, tools=[], registry={"adder": adder, "shouter": shouter}
    )

    assert tool_messages(result)[0]["content"] == "HI"


def test_tool_error_is_reported_back_instead_of_crashing_the_loop():
    # Behavior 7: a tool that raises becomes a tool result the model can react to,
    # rather than an exception that ends the session.
    def boom(**kwargs):
        raise ValueError("could not find that string")

    client = FakeClient([
        tool_turn(("c1", "boom", {})),
        text("recovered"),
    ])
    messages = [{"role": "user", "content": "go"}]

    result = run_agent(client, messages, tools=[], registry={"boom": boom})

    results = tool_messages(result)
    assert results[0]["tool_call_id"] == "c1"
    assert "could not find that string" in results[0]["content"]
    assert result[-1].content == "recovered"  # the loop kept going


def test_malformed_arguments_become_feedback_and_allow_another_turn():
    client = FakeClient([
        tool_turn(("bad-json", "read_file", "{not json}")),
        text("I need valid arguments."),
    ])

    result = run_agent(client, [], tools=[], registry={})

    assert tool_messages(result)[0]["tool_call_id"] == "bad-json"
    assert tool_messages(result)[0]["content"].startswith("Error:")
    assert len(client.calls) == 2


def test_next_request_contains_assistant_call_and_matching_tool_feedback():
    client = FakeClient([
        tool_turn(("r1", "read_file", {"path": "app.py"})),
        text("Inspected."),
    ])
    run_agent(client, [{"role": "user", "content": "Inspect app.py"}], [],
              {"read_file": lambda path: "actual source"})
    assert len(client.calls[0]["messages"]) == 1
    sent = client.calls[1]["messages"]
    assert sent[1].tool_calls[0].id == "r1"
    assert sent[2] == {"role": "tool", "tool_call_id": "r1", "content": "actual source"}
