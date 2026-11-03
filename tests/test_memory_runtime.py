"""Session commands and request assembly, observed through the runtime."""
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip('redis_agent_memory')
pytest.importorskip('redis_agent_playbook')
import runtime

ROOT = Path(__file__).resolve().parents[1]
LEARNER = SimpleNamespace(CAPTURE=False, RECALL=False, PLAYBOOK=False)


def test_new_session_reloads_agents_md_and_clears_the_conversation(tmp_path):
    (tmp_path / 'AGENTS.md').write_text('Use type hints.')
    app = runtime.Workshop(LEARNER, Mock(), None, None, 'owner', tmp_path, tmp_path / 'out')
    previous = app.state.session_id
    app.state.history = [{'role': 'user', 'content': 'I like Google-style docstrings.'}]
    app.state.last_request = [{'role': 'user', 'content': 'old request'}]
    (tmp_path / 'AGENTS.md').write_text('Use type hints.\nUse uv.')
    app.command('/new-session')
    assert app.state.session_id != previous and app.state.owner == 'owner'
    assert app.state.history == [] and app.state.last_request == []
    assert 'Use uv.' in app.state.instructions


def test_sessions_lists_stored_sessions_and_resume_restores_the_conversation(tmp_path, capsys):
    memory = Mock()
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    memory.list_sessions.return_value.items = ['old-session', app.state.session_id]
    app.command('/sessions')
    shown = capsys.readouterr().out
    assert 'old-session' in shown and '(current)' in shown
    memory.list_sessions.assert_called_once_with(filter_owner_id='owner')
    memory.get_session_memory.return_value.model_dump.return_value = {'events': [
        {'role': 'USER', 'actorId': 'owner', 'content': [{'text': 'I like Google-style docstrings.'}]},
        {'role': 'ASSISTANT', 'actorId': 'coding-assistant', 'content': [{'text': 'Noted.'}]},
    ]}
    app.command('/resume old-session')
    assert app.state.session_id == 'old-session'
    assert app.state.history == [
        {'role': 'user', 'content': 'I like Google-style docstrings.'},
        {'role': 'assistant', 'content': 'Noted.'},
    ]


def test_view_context_shows_each_message_of_the_latest_request(tmp_path, capsys):
    app = runtime.Workshop(LEARNER, Mock(), None, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/view-context')
    assert 'Nothing sent' in capsys.readouterr().out
    app.state.last_request = [
        {'role': 'system', 'content': 'You are a coding assistant.'},
        {'role': 'assistant', 'content': None, 'tool_calls': [{'function': {'name': 'read_file'}}]},
        {'role': 'user', 'content': 'Write a function'},
    ]
    app.command('/view-context')
    shown = capsys.readouterr().out
    assert '[1] system: You are a coding assistant.' in shown
    assert '(asks to run read_file)' in shown and '[3] user: Write a function' in shown


def test_verify_runs_the_project_tests(tmp_path, capsys):
    project = tmp_path / 'project'
    shutil.copytree(ROOT / 'project', project)
    app = runtime.Workshop(LEARNER, Mock(), None, None, 'owner', project, tmp_path / 'out')
    app.command('/verify')
    assert 'Tests failed.' in capsys.readouterr().out
    shutil.copy(ROOT / 'solutions/validator.py', project / 'validator.py')
    app.command('/verify')
    assert 'Tests passed.' in capsys.readouterr().out


def test_status_and_inspection_never_call_the_model(tmp_path, capsys):
    model, memory = Mock(), Mock()
    app = runtime.Workshop(LEARNER, model, memory, Mock(skill_id='ent_team'), 'owner', tmp_path, tmp_path / 'out')
    app.command('/status')
    app.command('/view-context')
    shown = capsys.readouterr().out
    assert 'owner' in shown and 'ent_team' in shown and 'Capture:  off' in shown
    assert not model.mock_calls and not memory.mock_calls


def test_missing_service_configuration_is_named(tmp_path):
    app = runtime.Workshop(LEARNER, Mock(), None, None, 'owner', tmp_path, tmp_path / 'out')
    with pytest.raises(ValueError, match='AGENT_MEMORY'):
        app.command('/memories')


def test_tools_cannot_edit_or_read_outside_project(tmp_path):
    project = tmp_path / 'project'; project.mkdir()
    secret = tmp_path / 'outside.txt'; secret.write_text('do not read')
    registry = runtime.project_tools(project)
    with pytest.raises(ValueError, match='outside'):
        registry['read_file']('../outside.txt')
    with pytest.raises(ValueError, match='outside'):
        registry['write_file']('../outside.txt', 'overwrite')
    assert secret.read_text() == 'do not read'


def test_memories_shows_short_ids_and_forget_deletes_by_id(tmp_path, capsys):
    memory = Mock()
    memory.search_long_term_memory.return_value.model_dump.return_value = {'items': [
        {'id': 'abc12345full', 'text': 'Prefers Google-style docstrings.', 'memoryType': 'coding_preference'}]}
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/memories')
    assert '[abc12345]' in capsys.readouterr().out
    app.command('/forget abc12345')
    memory.bulk_delete_long_term_memories.assert_called_once_with(memory_ids=['abc12345full'])
    assert 'Forgot' in capsys.readouterr().out
    with pytest.raises(ValueError, match='No memory'):
        app.command('/forget zzz')
