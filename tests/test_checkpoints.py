from tests.fakes import FakeClient, text, tool_turn


def test_one_round_trip_executes_read_and_matches_result_id():
    from checkpoints.stage2_one_tool import round_trip

    client = FakeClient([tool_turn(("read-1", "read_file", {"path": "note.txt"})), text("Found the note")])
    seen = []
    messages = round_trip(client, "Read note.txt", reader=lambda **args: seen.append(args) or "1: hello")
    assert seen == [{"path": "note.txt"}]
    assert messages[-2] == {"role": "tool", "tool_call_id": "read-1", "content": "1: hello"}
    assert len(client.calls) == 2


def test_one_round_trip_returns_tool_errors_as_feedback():
    from checkpoints.stage2_one_tool import round_trip

    def missing(**_):
        raise FileNotFoundError("missing.txt")

    client = FakeClient([tool_turn(("read-1", "read_file", {"path": "missing.txt"})), text("Missing file")])
    messages = round_trip(client, "Read missing.txt", reader=missing)
    assert "missing.txt" in messages[-2]["content"]


def test_plain_round_trip_exposes_only_a_path_before_paging_is_introduced():
    from checkpoints.stage2_one_tool import round_trip

    client = FakeClient([tool_turn(("read-1", "read_file", {"path": "brief.md"})), text("Read it")])
    round_trip(client, "Read brief.md", reader=lambda path: "actual file")

    schema = client.calls[0]["tools"][0]["function"]
    assert set(schema["parameters"]["properties"]) == {"path"}
    assert len(client.calls[0]["messages"]) == 1
    assert len(client.calls[1]["messages"]) == 3
    assert client.calls[1]["messages"][-1]["content"] == "actual file"


def test_paged_round_trip_exposes_the_improved_contract():
    from checkpoints.stage2_one_tool import round_trip

    client = FakeClient([tool_turn(("read-1", "read_file", {"path": "brief.md", "offset": 3, "limit": 2})), text("Read it")])
    seen = []
    round_trip(client, "Read brief.md", reader=lambda **args: seen.append(args) or "3: actual", paged=True)
    assert seen == [{"path": "brief.md", "offset": 3, "limit": 2}]
    schema = client.calls[0]["tools"][0]["function"]
    assert set(schema["parameters"]["properties"]) == {"path", "offset", "limit"}


def test_checkpoint_repeats_the_same_question_with_either_schema(monkeypatch):
    import sys
    from checkpoints import stage2_one_tool

    prompt = "What release decision is near line 180?"
    for options in ([], ["--paged"]):
        client = FakeClient([text("No tool in this prepared reply.")])
        monkeypatch.setattr(stage2_one_tool, "build_client", lambda: client)
        monkeypatch.setattr(sys, "argv", ["stage2", "--prompt", prompt, *options])
        stage2_one_tool.main()
        assert client.calls[0]["messages"] == [{"role": "user", "content": prompt}]
        assert "tool_choice" not in client.calls[0]


def test_checkpoint_default_question_matches_the_first_file_lesson(monkeypatch):
    import sys
    from checkpoints import stage2_one_tool

    client = FakeClient([text("reply supplied by the test transport")])
    monkeypatch.setattr(stage2_one_tool, "build_client", lambda: client)
    monkeypatch.setattr(sys, "argv", ["stage2"])
    stage2_one_tool.main()

    assert client.calls[0]["messages"] == [{
        "role": "user",
        "content": "Read checkpoints/project_brief.md. What is this project's release name?",
    }]


def test_follow_up_request_is_visible_but_not_executed_even_with_reply_text(capsys):
    from checkpoints.stage2_one_tool import round_trip

    follow_up = tool_turn(("read-2", "read_file", {"path": "release_log.md", "offset": 170, "limit": 20}))
    follow_up.content = "The brief points to another file."
    client = FakeClient([
        tool_turn(("read-1", "read_file", {"path": "project_brief.md"})),
        follow_up,
    ])
    reads = []
    messages = round_trip(
        client, "Read the brief and follow its release-decision reference.",
        reader=lambda **args: reads.append(args) or "See release_log.md, line 180.",
        paged=True,
    )

    output = capsys.readouterr().out
    assert "REQUEST read-2" in output
    assert "read_file" in output and '"offset": 170' in output
    assert "not executed: this checkpoint stops after one exchange" in output
    assert "RESULT read-2" not in output
    assert reads == [{"path": "project_brief.md"}]
    assert len(client.calls) == 2
    assert messages[-1].content == "The brief points to another file."
    assert messages[-1].tool_calls[0].id == "read-2"


def test_description_experiment_only_proposes_actions():
    from checkpoints.description_lab import compare_descriptions

    client = FakeClient([
        tool_turn(("weak", "run_bash", {"command": "cat note.txt"})),
        tool_turn(("clear", "read_file", {"path": "note.txt"})),
    ])
    proposals = compare_descriptions(client, "Read note.txt")
    assert [item["tools"] for item in proposals] == [["run_bash"], ["read_file"]]
    assert all(call["messages"][0]["content"] == "Read note.txt" for call in client.calls)
    descriptions = [call["tools"][0]["function"]["description"] for call in client.calls]
    assert descriptions[0] != descriptions[1]


def test_recovery_demonstrates_error_denial_and_failed_command(tmp_path):
    from checkpoints.recovery import run_recovery
    from solutions.agent import run_agent
    from solutions.tools import read_file

    messages = run_recovery(tmp_path, run_loop=run_agent, reader=read_file)
    results = [message["content"] for message in messages if isinstance(message, dict) and message.get("role") == "tool"]
    assert results[0].startswith("Error:")
    assert "right file" in results[1]
    assert "declined" in results[2]
    assert results[3].startswith("exit 3")
    assert "not verified" in messages[-1].content
