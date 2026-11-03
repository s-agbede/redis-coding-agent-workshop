"""Initialize learner files once; refresh supplied memory workshop code."""
from pathlib import Path
import shutil
import sys


def prepare_workspace(source: Path, workspace: Path) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for name in ('agent.py', 'project'):
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


if __name__ == '__main__':
    prepare_workspace(Path(sys.argv[1]), Path(sys.argv[2]))
