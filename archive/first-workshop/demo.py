"""Start the completed agent interactively: uv run python demo.py."""

import os
from pathlib import Path
import shutil
import sys
import tempfile
import subprocess

from preview import demo_preview


def main() -> None:
    root = Path(__file__).resolve().parent
    output = root / "output"
    output.mkdir(exist_ok=True)
    workspace = Path(tempfile.mkdtemp(prefix="demo-", dir=output))

    # Use ordinary copies so main.py imports the completed agent without
    # replacing the learner's file or adding a special mode to the runner.
    for name in ("main.py", "tools.py", "ui.py", "verify_capstone.py"):
        shutil.copy2(root / name, workspace / name)
    shutil.copy2(root / "solutions/agent.py", workspace / "agent.py")
    shutil.copytree(
        root / "capstone", workspace / "capstone",
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )

    print(f"Demo workspace: {workspace / 'capstone'}", flush=True)
    print("Type a task for the completed agent. Type exit to finish.", flush=True)
    print("Demo files are kept here after you exit; learner files are unchanged.", flush=True)

    # Reuse the configured environment and the normal interactive terminal.
    os.chdir(root)
    with demo_preview(workspace / "capstone"):
        try:
            subprocess.run([
                sys.executable, str(workspace / "main.py"),
                "--project", str(workspace / "capstone"),
            ], check=True)
        except KeyboardInterrupt:
            print("\nDemo finished; learner App Preview restored.")


if __name__ == "__main__":
    main()
