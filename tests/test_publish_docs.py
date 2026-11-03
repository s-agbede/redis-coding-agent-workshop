"""The publisher exposes one workshop and never modifies learner work."""
import shutil
import subprocess
import sys
from pathlib import Path
from scripts.publish_docs import LESSONS
ROOT = Path(__file__).resolve().parents[1]


def workspace(tmp_path: Path) -> Path:
    (tmp_path/'scripts').mkdir()
    shutil.copy2(ROOT/'scripts/publish_docs.py', tmp_path/'scripts/publish_docs.py')
    shutil.copy2(ROOT/'agent.py', tmp_path/'agent.py')  # lessons link to named places in it
    for name in ('docs', 'project', 'skills', 'solutions'):
        shutil.copytree(ROOT/name, tmp_path/name, ignore=shutil.ignore_patterns('__pycache__'))
    return tmp_path


def publish(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(root/'scripts/publish_docs.py'), *args],cwd=root,capture_output=True,text=True)


def test_single_workshop_order_slides_and_editor_paths(tmp_path):
    root=workspace(tmp_path)
    assert publish(root).returncode == 0
    public=root/'docker-workshop/frontend/public'
    manifest=(public/'build-steps/manifest.yaml').read_text()
    assert [line.split(': ',1)[1] for line in manifest.splitlines() if '- file:' in line] == list(LESSONS)
    recap=(public/'build-steps/01-recap.md').read_text()
    assert 'slides: /slides/01-recap.md' in recap
    assert (public/'slides/01-recap.md').is_file()
    assert 'editorFile: agent.py' in recap
    assert 'editorFile: project/AGENTS.md' in (public/'build-steps/02-forgetting.md').read_text()
    assert (public/'skills/report-validation/SKILL.md').is_file()
    assert (public/'project/tests/test_validator.py').is_file()
    assert not (public/'part2').exists()
    assert 'title: Give a coding agent useful memory' in (public/'welcome.md').read_text()
    assert publish(root,'--check').returncode == 0


def test_publication_preserves_learner_edits_and_repairs_generated_drift(tmp_path):
    root=workspace(tmp_path)
    learner=root/'.workshop/project';learner.mkdir(parents=True)
    (learner/'validator.py').write_text('# learner edit')
    (root/'.workshop/agent.py').write_text('# learner agent')
    assert publish(root).returncode == 0
    target=root/'docker-workshop/frontend/public/build-steps/01-recap.md'
    target.write_text('outdated')
    assert publish(root,'--check').returncode == 1
    assert target.read_text() == 'outdated'
    assert publish(root).returncode == 0
    assert (learner/'validator.py').read_text() == '# learner edit'
    assert (root/'.workshop/agent.py').read_text() == '# learner agent'


def test_retired_generated_lessons_removed_but_custom_asset_preserved(tmp_path):
    root=workspace(tmp_path)
    old=root/'docker-workshop/frontend/public/build-steps/01-first-call.md'
    old.parent.mkdir(parents=True);old.write_text('old')
    custom=old.parent.parent/'custom.svg';custom.write_text('<svg/>')
    assert publish(root,'--check').returncode == 1
    assert old.exists()
    assert publish(root).returncode == 0
    assert not old.exists()
    assert custom.read_text() == '<svg/>'


def test_files_the_sources_no_longer_produce_are_removed(tmp_path):
    root = workspace(tmp_path)
    public = root/'docker-workshop/frontend/public'
    stale = [public/'solutions/steps/01-capture.py', public/'images/slides/99-old.jpg', root/'docker-workshop/docs/images/slides/99-old.jpg']
    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('old')
    assert publish(root, '--check').returncode == 1
    assert publish(root).returncode == 0
    assert not any(path.exists() for path in stale)
    assert (public/'solutions/validator.py').is_file()
    assert publish(root, '--check').returncode == 0
