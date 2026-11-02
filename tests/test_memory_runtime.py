"""Observable session and context behavior through the Part 2 runtime."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip('redis_agent_memory')
pytest.importorskip('redis_agent_playbook')


def runtime_module():
    import runtime
    return runtime


def test_new_session_reloads_project_and_clears_request_and_history(tmp_path):
    runtime = runtime_module()
    instructions = tmp_path / 'AGENTS.md'
    instructions.write_text('Use uv.')
    session = runtime.Session.start('learner-a', tmp_path)
    previous = session.session_id
    session.history = [{'role': 'user', 'content': 'Remember my preference'}]
    session.last_request = [{'role': 'user', 'content': 'old request'}]
    session.preferences = [{'text': 'old memory'}]
    instructions.write_text('Use uv. Preserve tests.')
    fresh = session.reset()
    assert fresh.owner == 'learner-a'
    assert fresh.session_id != previous
    assert fresh.history == [] and fresh.last_request == [] and fresh.preferences == []
    assert 'Preserve tests.' in fresh.instructions


def test_context_preserves_project_task_and_history_without_stale_memory(tmp_path):
    runtime = runtime_module()
    (tmp_path / 'AGENTS.md').write_text('Use uv.')
    state = runtime.Session.start('owner', tmp_path)
    state.history = [{'role': 'user', 'content': 'Earlier task'}, {'role': 'assistant', 'content': 'Earlier answer'}]
    learner = Mock()
    learner.preference_context.side_effect = lambda items: str(items)
    learner.skill_context.return_value = ''
    state.preferences = [{'text': 'Explain checks in comments'}]
    messages = runtime.compose(state, learner, 'Validate columns')
    assert 'Use uv.' in messages[0]['content']
    assert 'Explain checks in comments' in messages[1]['content']
    assert messages[-1] == {'role': 'user', 'content': 'Validate columns'}
    assert messages[-2]['content'] == 'Earlier answer'
    assert len(state.history) == 2
    state.preferences = []
    assert 'Explain checks' not in str(runtime.compose(state, learner, 'Another task'))


def test_commands_never_call_model_or_record_events(tmp_path):
    runtime = runtime_module()
    learner, model, memory = Mock(), Mock(), Mock()
    app = runtime.Workshop(learner, model, memory, None, 'owner', tmp_path, tmp_path / 'output')
    app.command('/view-context')
    app.command('/new-session')
    assert not model.mock_calls and not memory.mock_calls and not learner.mock_calls


def test_tools_cannot_edit_or_read_outside_project(tmp_path):
    runtime = runtime_module()
    project = tmp_path / 'project'; project.mkdir()
    secret = tmp_path / 'outside.txt'; secret.write_text('do not read')
    registry = runtime.project_tools(project)
    with pytest.raises(ValueError, match='outside'):
        registry['read_file']('../outside.txt')
    with pytest.raises(ValueError, match='outside'):
        registry['write_file']('../outside.txt', 'overwrite')
    assert secret.read_text() == 'do not read'


def test_status_explains_stage_and_configuration_without_service_calls(tmp_path, capsys):
    runtime = runtime_module()
    learner = SimpleNamespace(CAPTURE_ENABLED=False, RECALL_ENABLED=False, PLAYBOOK_ENABLED=False)
    model, memory, playbook = Mock(), Mock(), Mock(skill_id='ent_team')
    app = runtime.Workshop(learner, model, memory, playbook, 'learner-a', tmp_path, tmp_path/'output')
    app.command('/status')
    shown = capsys.readouterr().out
    assert 'learner-a' in shown and app.state.session_id in shown
    assert 'commenting preference' in shown
    assert 'not live-checked' in shown and 'ent_team' in shown
    assert not model.mock_calls and not memory.mock_calls and not playbook.mock_calls
    learner.CAPTURE_ENABLED=True
    learner.RECALL_ENABLED=True
    app.command('/status')
    assert '/skills' in capsys.readouterr().out


def test_status_names_missing_configuration_before_memory_exercise(tmp_path, capsys):
    runtime = runtime_module()
    learner=SimpleNamespace(CAPTURE_ENABLED=True,RECALL_ENABLED=False,PLAYBOOK_ENABLED=False)
    app=runtime.Workshop(learner,Mock(),None,None,'owner',tmp_path,tmp_path/'output')
    app.command('/status')
    assert 'instructor' in capsys.readouterr().out
