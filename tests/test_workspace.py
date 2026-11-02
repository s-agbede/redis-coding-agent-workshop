"""Rebuilds preserve the learner's agent and both project directories."""
from pathlib import Path
from scripts.prepare_workspace import prepare_workspace


def test_workspace_preserves_student_work_and_refreshes_supplied_runtime(tmp_path: Path):
    source=tmp_path/'source';source.mkdir()
    for folder in ('project','project-review','solutions','challenge','skills','docs'):
        (source/folder).mkdir()
        (source/folder/'example.py').write_text('original')
    for name in ('agent.py','main.py','runtime.py','context.py','playbook.py'):
        (source/name).write_text('original')
    target=tmp_path/'workspace'
    prepare_workspace(source,target)
    for name in ('agent.py','project/example.py','project-review/example.py'):
        (target/name).write_text('learner edit')
    (source/'runtime.py').write_text('new runtime')
    (source/'skills/example.py').write_text('new supplied skill')
    prepare_workspace(source,target)
    for name in ('agent.py','project/example.py','project-review/example.py'):
        assert (target/name).read_text() == 'learner edit'
    assert (target/'runtime.py').read_text() == 'new runtime'
    assert (target/'skills/example.py').read_text() == 'new supplied skill'
    assert (target/'challenge/example.py').is_file()
    assert not (target/'part2').exists()
