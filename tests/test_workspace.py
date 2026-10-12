"""A rebuild refreshes supplied code without erasing learner work."""
from pathlib import Path

from scripts.prepare_workspace import prepare_workspace


def test_workspace_has_one_source_and_preserves_learner_files(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    for name in ("agent.py", "main.py", "tools.py", "pyproject.toml", "uv.lock"):
        (source / name).write_text("original")
    for directory in ("capstone", "solutions", "tests", "checkpoints"):
        (source / directory).mkdir()
        (source / directory / "example.py").write_text("original")
    workspace = tmp_path / "learner"
    prepare_workspace(source, workspace)
    (workspace / "agent.py").write_text("learner agent")
    (workspace / "capstone/example.py").write_text("learner repair")
    (source / "main.py").write_text("updated helper")
    (source / "solutions/example.py").write_text("updated solution")
    (source / "fizzbuzz.py").write_text("presenter scratch")
    (workspace / "fizzbuzz.py").write_text("learner scratch")
    prepare_workspace(source, workspace)
    assert (workspace / "fizzbuzz.py").read_text() == "learner scratch"
    assert (workspace / "agent.py").read_text() == "learner agent"
    assert (workspace / "capstone/example.py").read_text() == "learner repair"
    assert (workspace / "main.py").read_text() == "updated helper"
    assert (workspace / "solutions/example.py").read_text() == "updated solution"
