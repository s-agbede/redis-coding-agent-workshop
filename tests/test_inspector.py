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


def test_the_page_answers_the_workbench_readiness_check(inspector):
    import threading
    from http.server import ThreadingHTTPServer
    from urllib.request import Request, urlopen
    module, _ = inspector
    server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        url = f'http://127.0.0.1:{server.server_address[1]}/memory/'
        assert urlopen(Request(url, method='HEAD')).status == 200
        assert b'Agent Memory' in urlopen(url).read()
    finally:
        server.shutdown()


def test_store_settings_are_read_only_unless_editing_is_switched_on(inspector, monkeypatch):
    module, _ = inspector
    monkeypatch.delenv('INSPECTOR_ALLOW_EDITS', raising=False)
    with pytest.raises(PermissionError):
        module.update_setting('summarization', {'enabled': True})


def test_an_edit_sends_only_that_setting_and_shows_what_the_store_now_holds(inspector, monkeypatch):
    module, _ = inspector
    monkeypatch.setenv('INSPECTOR_ALLOW_EDITS', '1')
    sent = []
    monkeypatch.setattr(module, 'control_plane', lambda method, body=None: sent.append((method, body)) or {
        'storeId': 's1', 'summarization': {'enabled': True}, 'adminSecret': 'never shown'})
    result = module.update_setting('summarization', {'enabled': True})
    assert sent == [('PATCH', {'summarization': {'enabled': True}}), ('GET', None)]
    assert result['settings'] == {'summarization': {'enabled': True}} and result['editable'] is True
    with pytest.raises(module.ControlPlaneRejected):
        module.update_setting('customMemoryTypes', [])


def test_prompt_edits_use_the_strategy_operation_and_catch_silent_ignores(inspector, monkeypatch):
    module, _ = inspector
    monkeypatch.setenv('INSPECTOR_ALLOW_EDITS', '1')
    stored = {'storeId': 's1', 'customMemoryTypes': [{'name': 'coding_preference', 'extractionStrategy': {'prompt': 'old'}}]}
    sent = []
    monkeypatch.setattr(module, 'control_plane', lambda method, body=None: sent.append(body) or stored)
    with pytest.raises(module.ControlPlaneRejected, match='does not show it'):
        module.update_prompt('coding_preference', 'new')
    assert sent[0] == {'updateCustomMemoryTypeStrategies': [{'typeName': 'coding_preference', 'prompt': 'new'}]}
    stored['customMemoryTypes'][0]['extractionStrategy']['prompt'] = 'new'
    assert module.update_prompt('coding_preference', 'new')['settings']['customMemoryTypes'][0]['extractionStrategy']['prompt'] == 'new'


def test_you_can_forget_your_own_memories_but_not_someone_elses(inspector):
    module, client = inspector
    client.get_long_term_memory.return_value.model_dump.return_value = {'id': 'm1', 'ownerId': 'learner-a'}
    assert module.forget('m1') == {'forgotten': 'm1'}
    client.bulk_delete_long_term_memories.assert_called_once_with(memory_ids=['m1'])
    client.get_long_term_memory.return_value.model_dump.return_value = {'id': 'm2', 'ownerId': 'learner-b'}
    with pytest.raises(PermissionError):
        module.forget('m2')
    assert client.bulk_delete_long_term_memories.call_count == 1
