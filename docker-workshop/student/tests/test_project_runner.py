from pathlib import Path

import pytest


def test_project_instructions_and_verification_report_are_explicit(tmp_path):
    from main import build_system_prompt

    (tmp_path / "AGENTS.md").write_text("Run python ../verify_capstone.py --project .\n")
    prompt = build_system_prompt(tmp_path)
    assert "python ../verify_capstone.py" in prompt
    assert "Changed files" in prompt
    assert "Unverified" in prompt
    assert "pre-existing" in prompt


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
