"""The Agent Memory inspector shows only this workspace's owner's data."""
import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import pytest

pytest.importorskip('redis_agent_memory')
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def inspector(tmp_path, monkeypatch):
    (tmp_path / 'output/workshop').mkdir(parents=True)
    (tmp_path / 'output/workshop/owner.json').write_text(json.dumps({'owner': 'learner-a'}))
    monkeypatch.setenv('WORKSPACE_ROOT', str(tmp_path))
    monkeypatch.delenv('IRIS_OWNER_ID', raising=False)
    monkeypatch.delenv('AGENT_MEMORY_CONTROL_PLANE_URL', raising=False)
    spec = importlib.util.spec_from_file_location('inspector', ROOT / 'agent-memory/inspector.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    client = Mock()
    monkeypatch.setattr(module, 'memory', lambda: client)
    return module, client


def test_sessions_and_memories_are_filtered_by_the_workspace_owner(inspector):
    module, client = inspector
    client.list_sessions.return_value.items = ['s1']
    client.search_long_term_memory.return_value.model_dump.return_value = {'items': [
        {'text': 'The user prefers Google-style docstrings.', 'memoryType': 'user_preference'}]}
    assert module.sessions() == {'owner': 'learner-a', 'sessions': ['s1']}
    client.list_sessions.assert_called_with(filter_owner_id='learner-a')
    assert module.memories()['memories'][0]['type'] == 'user_preference'
    assert client.search_long_term_memory.call_args.kwargs['request']['filter_'] == {'owner_id': {'eq': 'learner-a'}}


def test_another_owners_session_is_refused(inspector):
    module, client = inspector
    client.get_session_memory.return_value.model_dump.return_value = {'ownerId': 'learner-b', 'events': []}
    with pytest.raises(PermissionError):
        module.session('their-session')


def test_store_settings_explain_they_need_self_hosting(inspector):
    module, _ = inspector
    assert module.settings()['available'] is False
