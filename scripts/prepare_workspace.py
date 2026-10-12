"""Create learner files once; refresh supplied code from the repository source."""
from pathlib import Path
import shutil
import sys


def prepare_workspace(source: Path, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    # These are the learner's work. Never replace existing files, even on rebuild.
    for name in ("agent.py", "capstone"):
        origin = source / name
        destination = workspace / name
        if not destination.exists():
            if origin.is_dir():
                shutil.copytree(origin, destination)
            else:
                shutil.copy2(origin, destination)
    for name in ("main.py", "tools.py", "ui.py", "demo.py", "preview.py", "check_setup.py", "verify_capstone.py"):
        if (source / name).is_file():
            shutil.copy2(source / name, workspace / name)
    for name in ("pyproject.toml", "uv.lock", "README.md", "WORKSHOP.md", "FACILITATOR.md"):
        if (source / name).is_file():
            shutil.copy2(source / name, workspace / name)
    for name in ("solutions", "tests", "checkpoints"):
        shutil.copytree(
            source / name, workspace / name, dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )


if __name__ == "__main__":
    prepare_workspace(Path(sys.argv[1]), Path(sys.argv[2]))
