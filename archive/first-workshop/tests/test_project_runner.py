from pathlib import Path

import pytest


def test_project_instructions_are_added_without_extra_coaching(tmp_path):
    from main import SYSTEM_PROMPT, build_system_prompt

    (tmp_path / "AGENTS.md").write_text("Run python ../verify_capstone.py --project .\n")
    prompt = build_system_prompt(tmp_path)
    assert prompt == SYSTEM_PROMPT + "\n\nProject instructions:\n" + (tmp_path / "AGENTS.md").read_text()


def test_project_directory_restores_cwd_after_error(tmp_path):
    from main import project_directory

    previous = Path.cwd()
    with pytest.raises(RuntimeError):
        with project_directory(tmp_path):
            assert Path.cwd() == tmp_path.resolve()
            raise RuntimeError("test exit")
    assert Path.cwd() == previous


def test_project_without_instructions_uses_base_prompt(tmp_path):
    from main import build_system_prompt

    assert "Project instructions" not in build_system_prompt(tmp_path)


def test_unexecuted_tool_request_returns_to_shell_without_claiming_an_answer(tmp_path, monkeypatch):
    import main
    from tests.fakes import FakeClient, tool_turn

    pending = tool_turn(("find", "list_files", {}))
    pending.content = "I will inspect the files."
    client = FakeClient([pending])
    prompts = []
    answers = []
    def prompt():
        prompts.append("asked")
        return "inspect" if len(prompts) == 1 else "exit"
    def run(client, messages, tools, registry, max_iters):
        messages.append(client.chat.completions.create(model="test", messages=messages).choices[0].message)
    monkeypatch.setattr(main, "run_agent", run)
    monkeypatch.setattr(main.ui, "prompt_user", prompt)
    monkeypatch.setattr(main.ui, "show_answer", answers.append)
    main.interactive_session(client, tmp_path)
    assert prompts == ["asked"], "Unanswered tool calls must not leak into a follow-up request"
    assert answers == [], "Intent alongside a tool request is not a final answer"


def test_discovery_prompt_does_not_reveal_the_evidence_directory(tmp_path):
    from main import SYSTEM_PROMPT, build_system_prompt

    (tmp_path / "checkpoints").mkdir()
    assert build_system_prompt(tmp_path) == SYSTEM_PROMPT
