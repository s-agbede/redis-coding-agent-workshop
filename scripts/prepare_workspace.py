"""Initialize learner files once; refresh supplied memory workshop code.

    python3 scripts/prepare_workspace.py SOURCE WORKSPACE           # normal start: keeps learner work
    python3 scripts/prepare_workspace.py --reset SOURCE WORKSPACE   # back to the workshop's starting point
"""
from datetime import datetime
from pathlib import Path
import shutil
import sys

LEARNER_FILES = ('agent.py', 'project')
OWNER_FILE = Path('output/workshop/owner.json')


def prepare_workspace(source: Path, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for name in LEARNER_FILES:
        origin, destination = source / name, workspace / name
        if origin.exists() and not destination.exists():
            if origin.is_dir():
                shutil.copytree(origin, destination)
            else:
                shutil.copy2(origin, destination)
    for name in ('main.py', 'runtime.py', 'context.py', 'playbook.py', 'completion.py', 'tools.py', 'ui.py',
                 'pyproject.toml', 'uv.lock', 'README.md', 'WORKSHOP.md', 'FACILITATOR.md'):
        if (source / name).is_file():
            shutil.copy2(source / name, workspace / name)
    for name in ('solutions', 'tests', 'skills', 'docs', 'scripts'):
        if (source / name).is_dir():
            shutil.copytree(source / name, workspace / name, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))


def reset_workspace(source: Path, workspace: Path) -> Path:
    """Move the learner's agent.py, project and identity into a backup, then start fresh.

    Without its identity file the agent picks a new owner ID on its next start, so earlier
    memories and sessions stay in Redis Agent Memory but no longer belong to this learner.
    """
    backup = workspace / '.backups' / datetime.now().strftime('reset-%Y%m%d-%H%M%S')
    backup.mkdir(parents=True)
    for name in (*LEARNER_FILES, OWNER_FILE):
        current = workspace / name
        if current.exists():
            shutil.move(current, backup / Path(name).name)
    prepare_workspace(source, workspace)
    return backup


if __name__ == '__main__':
    arguments = sys.argv[1:]
    if arguments[:1] == ['--reset']:
        print(f'Reset. Your previous files are in {reset_workspace(Path(arguments[1]), Path(arguments[2]))}')
    else:
        prepare_workspace(Path(arguments[0]), Path(arguments[1]))
