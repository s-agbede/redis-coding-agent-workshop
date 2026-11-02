"""The presenter can launch the finished agent without replacing learner files."""
import os
from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_demo_starts_completed_agent_and_preserves_each_workspace(tmp_path):
    for name in ("demo.py", "preview.py", "main.py", "ui.py", "tools.py", "verify_capstone.py"):
        shutil.copy2(ROOT / name, tmp_path / name)
    shutil.copytree(ROOT / "solutions", tmp_path / "solutions")
    shutil.copytree(ROOT / "capstone", tmp_path / "capstone")
    starter = "raise RuntimeError('The demo must not load the learner agent')\n"
    (tmp_path / "agent.py").write_text(starter)
    original_app = (tmp_path / "capstone/app.py").read_bytes()

    env = {**os.environ, "AGENT_API_KEY": "unused-demo-test-key", "WORKSHOP_PREVIEW_FILE": str(tmp_path / "preview-selection")}
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(tmp_path / "demo.py")],
            input="exit\n", text=True, capture_output=True, env=env, cwd=tmp_path,
            timeout=15,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "Demo workspace:" in result.stdout

    workspaces = sorted((tmp_path / "output").glob("demo-*"))
    assert len(workspaces) == 2
    for workspace in workspaces:
        assert (workspace / "agent.py").read_bytes() == (ROOT / "solutions/agent.py").read_bytes()
        assert (workspace / "verify_capstone.py").is_file()
        assert (workspace / "capstone/app.py").read_bytes() == original_app

    (workspaces[0] / "capstone/app.py").write_text("# demo edit\n")
    assert (workspaces[1] / "capstone/app.py").read_bytes() == original_app
    assert (tmp_path / "capstone/app.py").read_bytes() == original_app
    assert (tmp_path / "agent.py").read_text() == starter
