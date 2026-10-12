"""Publishing updates documentation without touching a learner's program."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def workspace(tmp_path: Path) -> Path:
    script = ROOT / "scripts/publish_docs.py"
    assert script.is_file(), "The documentation publisher has not been implemented"
    (tmp_path / "scripts").mkdir()
    shutil.copy2(script, tmp_path / "scripts/publish_docs.py")
    shutil.copytree(ROOT / "docs", tmp_path / "docs")
    for name in ("README.md", "FACILITATOR.md", "WORKSHOP.md"):
        shutil.copy2(ROOT / name, tmp_path / name)
    return tmp_path


def publish(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(root / "scripts/publish_docs.py"), *args],
        cwd=root, capture_output=True, text=True, check=False,
    )


def test_publishing_copies_docs_and_preserves_learner_edits(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    student = root / ".workshop"
    (student / "capstone").mkdir(parents=True)
    for file in (student / "agent.py", student / "capstone/app.py"):
        file.write_text("# learner changes\n")
    result = publish(root)
    assert result.returncode == 0, result.stdout + result.stderr
    for directory in (root / "docker-workshop/docs",):
        assert (directory / "tasks/01-first-call.md").read_bytes() == (root / "docs/tasks/01-first-call.md").read_bytes()
    public = root / "docker-workshop/frontend/public"
    lesson = (public / "build-steps/01-first-call.md").read_text()
    assert lesson.startswith("---\ntitle: Make your first model call\neditorFile: agent.py\n---\n")
    assert "# Make your first model call\n" not in lesson
    assert "](/images/model-call.svg)" in lesson
    assert not (public / "build-steps/02-chat-loop.md").exists()
    assert (public / "welcome.md").read_bytes() == (root / "docs/welcome.md").read_bytes()
    assert (public / "images/model-call.svg").read_bytes() == (root / "docs/images/model-call.svg").read_bytes()
    assert not (student / "docs").exists()
    assert not (student / "README.md").exists()
    assert (student / "agent.py").read_text() == "# learner changes\n"
    assert (student / "capstone/app.py").read_text() == "# learner changes\n"
    assert not (student / "docs/research").exists()
    assert publish(root, "--check").returncode == 0


def test_check_reports_drift_without_writing_and_publish_repairs_it(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    assert publish(root).returncode == 0
    lesson = root / "docker-workshop/frontend/public/build-steps/01-first-call.md"
    lesson.write_text("outdated\n")
    result = publish(root, "--check")
    assert result.returncode == 1
    assert "build-steps/01-first-call.md" in result.stdout
    assert lesson.read_text() == "outdated\n"
    assert publish(root).returncode == 0
    assert publish(root, "--check").returncode == 0


def test_publisher_removes_retired_generated_pages_only(tmp_path: Path) -> None:
    root = workspace(tmp_path)
    old_pages = [
        root / "docker-workshop/docs/tasks/task-1.md",
        root / "docker-workshop/frontend/public/build-steps/02-chat-loop.md",
    ]
    for path in old_pages:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("retired lesson\n")
    asset = root / "docker-workshop/frontend/public/custom.svg"
    asset.write_text("keep this asset\n")
    learner_notes = root / ".workshop/docs/notes.md"
    learner_notes.parent.mkdir(parents=True)
    learner_notes.write_text("keep learner notes\n")
    assert publish(root, "--check").returncode == 1
    assert all(path.exists() for path in old_pages)
    assert publish(root).returncode == 0
    assert all(not path.exists() for path in old_pages)
    assert asset.read_text() == "keep this asset\n"
    assert learner_notes.read_text() == "keep learner notes\n"
    assert publish(root, "--check").returncode == 0
