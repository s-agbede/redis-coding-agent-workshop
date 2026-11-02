"""Check local workshop readiness without sending a model request or printing keys."""

import importlib.util
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SetupCheck:
    label: str
    passed: bool
    detail: str


def inspect_setup(root: Path, environ: Mapping[str, str]) -> list[SetupCheck]:
    """Inspect files, installed modules and key presence; perform no network I/O."""
    files = ("main.py", "tools.py", "agent.py", "runtime.py", "context.py", "playbook.py", "project/validator.py", "project/sample_report.json", "challenge/check_contract.py")
    checks = [
        SetupCheck("Python", sys.version_info >= (3, 10), "Python 3.10+ required; Docker supplies it."),
        SetupCheck(
            "Workspace", all((root / name).is_file() for name in files),
            "Run from the workshop root (/workspace in the browser Terminal), not inside project/.",
        ),
    ]
    for module in ("openai", "rich", "dotenv", "redis_agent_memory", "redis_agent_playbook", "pytest"):
        installed = importlib.util.find_spec(module) is not None
        checks.append(SetupCheck(
            module, installed, "Installed." if installed else "Run uv sync --group iris, then retry.",
        ))
    key = environ.get("AGENT_API_KEY", "").strip()
    configured = bool(key) and key not in {"sk-...", "your-api-key-here", "your-api-key"}
    checks.append(SetupCheck(
        "Model key", configured,
        "Key found, but not validated: this check has not tried your AI service. The first live exercise tests whether it works."
        if configured else
        "Ask your instructor to configure AGENT_API_KEY for this workspace before running a model exercise. "
        "This local check does not contact the model service.",
    ))
    return checks


def format_report(checks: Sequence[SetupCheck]) -> str:
    lines = ["Local setup check — no model request is made."]
    lines.extend(f"{'OK' if check.passed else 'MISSING'} {check.label}: {check.detail}" for check in checks)
    lines.append("The coding loop is supplied. Memory exercises start disabled; /status shows the current checkpoint.")
    return "\n".join(lines)


def main() -> int:
    # Dependency inspection still works when python-dotenv is absent.
    if importlib.util.find_spec("dotenv") is not None:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=".env")
    checks = inspect_setup(Path.cwd(), os.environ)
    print(format_report(checks))
    return 0 if all(check.passed for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
