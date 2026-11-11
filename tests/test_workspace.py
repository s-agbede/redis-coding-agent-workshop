import json
"""Rebuilds preserve the learner's agent and project."""
from pathlib import Path
from scripts.prepare_workspace import prepare_workspace, reset_workspace


def test_workspace_preserves_student_work_and_refreshes_supplied_runtime(tmp_path: Path):
    source=tmp_path/'source';source.mkdir()
    for folder in ('project','solutions','skills','docs'):
        (source/folder).mkdir()
        (source/folder/'example.py').write_text('original')
    for name in ('agent.py','main.py','runtime.py','context.py','playbook.py'):
        (source/name).write_text('original')
    target=tmp_path/'workspace'
    prepare_workspace(source,target)
    for name in ('agent.py','project/example.py'):
        (target/name).write_text('learner edit')
    (source/'runtime.py').write_text('new runtime')
    (source/'skills/example.py').write_text('new supplied skill')
    prepare_workspace(source,target)
    for name in ('agent.py','project/example.py'):
        assert (target/name).read_text() == 'learner edit'
    assert (target/'runtime.py').read_text() == 'new runtime'
    assert (target/'skills/example.py').read_text() == 'new supplied skill'
    assert not (target/'part2').exists()


def test_reset_restores_the_starting_point_and_keeps_a_backup(tmp_path: Path):
    source = tmp_path/'source'; (source/'project').mkdir(parents=True)
    (source/'agent.py').write_text('CAPTURE = False')
    (source/'project/AGENTS.md').write_text('Python with type hints.')
    target = tmp_path/'workspace'
    prepare_workspace(source, target)
    (target/'agent.py').write_text('CAPTURE = True')
    (target/'project/AGENTS.md').write_text('Python with type hints.\nGoogle-style docstrings.')
    (target/'project/fizzbuzz.py').write_text('made by the agent')
    (target/'output/workshop').mkdir(parents=True)
    (target/'output/workshop/owner.json').write_text('{"owner": "old"}')

    backup = reset_workspace(source, target)

    assert (target/'agent.py').read_text() == 'CAPTURE = False'
    assert (target/'project/AGENTS.md').read_text() == 'Python with type hints.'
    assert not (target/'project/fizzbuzz.py').exists()
    assert not (target/'output/workshop/owner.json').exists()  # a new learner identity next start
    assert (backup/'agent.py').read_text() == 'CAPTURE = True'
    assert (backup/'project/fizzbuzz.py').is_file() and (backup/'owner.json').is_file()
    assert not backup.is_relative_to(target/'project')
    # The agent's next start deletes the previous learner's memories and sessions.
    assert json.loads((target/'output/workshop/forget.json').read_text()) == {'owner': 'old'}
