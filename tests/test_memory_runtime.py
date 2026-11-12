"""Session commands and request assembly, observed through the runtime."""
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
    memory.list_sessions.return_value.items = [SimpleNamespace(session_id=s) for s in ['old-session', app.state.session_id]]
    memory.get_session_memory.return_value.model_dump.return_value = {'events': [
        {'role': 'USER', 'actorId': 'owner', 'content': [{'text': 'I like Google-style docstrings.'}]},
        {'role': 'ASSISTANT', 'actorId': 'coding-assistant', 'content': [{'text': 'Noted.'}]},
    ]}
    app.command('/sessions')
    shown = capsys.readouterr().out
    assert 'old-sess  I like Google-style docstrings.' in shown and '(current)' in shown
    memory.list_sessions.assert_called_once_with(owner_id='owner')
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
        {'memoryId': 'abc12345full', 'text': 'Prefers Google-style docstrings.', 'memoryType': 'coding_preference'}]}
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/memories')
    assert '[abc12345]' in capsys.readouterr().out
    app.command('/forget abc12345')
    memory.bulk_delete_long_term_memories.assert_called_once_with(memory_ids=['abc12345full'])
    assert 'Forgot' in capsys.readouterr().out
    with pytest.raises(ValueError, match='No memory'):
        app.command('/forget zzz')


def session_not_found() -> Exception:
    import httpx
    from redis_agent_memory import errors
    data = errors.NotFoundErrorResponseContentData.model_construct(title='Session Not Found', status=404)
    return errors.NotFoundErrorResponseContent(data, httpx.Response(404, request=httpx.Request('GET', 'http://memory')))


def test_events_explains_a_session_nothing_was_recorded_for(tmp_path, capsys):
    memory = Mock()
    memory.get_session_memory.side_effect = session_not_found()
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/events')
    assert 'Nothing recorded for this session yet' in capsys.readouterr().out


def test_resume_names_a_session_that_does_not_exist(tmp_path):
    memory = Mock()
    memory.list_sessions.return_value.items = [SimpleNamespace(session_id='missing-id')]
    memory.get_session_memory.side_effect = session_not_found()
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    with pytest.raises(ValueError, match='No stored session missing-id'):
        app.command('/resume missing-id')


def stored_sessions(memory: Mock, sessions: dict[str, str]) -> None:
    """Agent Memory with these sessions, each holding one user message."""
    memory.list_sessions.return_value.items = [SimpleNamespace(session_id=s) for s in sessions]
    def session(session_id: str) -> Mock:
        found = Mock()
        found.model_dump.return_value = {'events': [
            {'role': 'USER', 'actorId': 'owner', 'content': [{'text': sessions[session_id]}]}]}
        return found
    memory.get_session_memory.side_effect = lambda session_id: session(session_id)


def test_sessions_are_numbered_and_labelled_by_their_first_message(tmp_path, capsys):
    memory = Mock()
    stored_sessions(memory, {'3f9a1c2e' + '0' * 24: 'Write a slug function', 'b6c0a46e' + '1' * 24: 'Show me FizzBuzz'})
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/sessions')
    shown = capsys.readouterr().out
    assert '1  3f9a1c2e  Write a slug function' in shown
    assert '2  b6c0a46e  Show me FizzBuzz' in shown


def test_resume_accepts_a_list_number_or_the_start_of_an_id(tmp_path):
    memory = Mock()
    first, second = '3f9a1c2e' + '0' * 24, 'b6c0a46e' + '1' * 24
    stored_sessions(memory, {first: 'Write a slug function', second: 'Show me FizzBuzz'})
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/resume 2')
    assert app.state.session_id == second
    app.command('/resume 3f9a')
    assert app.state.session_id == first
    with pytest.raises(ValueError, match='No stored session 9'):
        app.command('/resume 9')


def fake_memory_with_bookmark(status_code: int, value: str | None = None) -> SimpleNamespace:
    """An SDK-shaped client whose HTTP client answers the extraction-bookmark request."""
    requested = []
    def get(url, headers):
        requested.append((url, headers))
        return SimpleNamespace(status_code=status_code, json=lambda: {'value': value})
    config = SimpleNamespace(server_url='http://memory', globals=SimpleNamespace(store_id='store-1'),
                             security=SimpleNamespace(api_key='key-1'), client=SimpleNamespace(get=get))
    return SimpleNamespace(sdk_configuration=config, requested=requested)


def test_extraction_is_up_to_date_once_its_bookmark_reaches_the_last_event():
    memory = fake_memory_with_bookmark(200, 'event-9')
    assert runtime.extraction_status(memory, 'session-1', 'event-9') == 'up to date'
    url, headers = memory.requested[0]
    assert url == ('http://memory/v1/stores/store-1/session-memory/session-1/properties/'
                   'custom_extracted_up_to_event_id_coding_preference')
    assert headers == {'Authorization': 'Bearer key-1'}
    assert runtime.extraction_status(fake_memory_with_bookmark(200, 'event-8'), 'session-1', 'event-9') == 'pending'
    assert runtime.extraction_status(fake_memory_with_bookmark(404), 'session-1', 'event-9') == 'pending'


def test_events_ends_with_whether_extraction_has_caught_up(tmp_path, capsys, monkeypatch):
    memory = Mock()
    memory.get_session_memory.return_value.model_dump.return_value = {'events': [
        {'eventId': 'event-9', 'role': 'USER', 'actorId': 'owner', 'content': [{'text': 'I like Google-style docstrings.'}]}]}
    monkeypatch.setattr(runtime, 'extraction_status', lambda client, session_id, last: 'pending')
    app = runtime.Workshop(LEARNER, Mock(), memory, None, 'owner', tmp_path, tmp_path / 'out')
    app.command('/events')
    assert 'Extraction: pending' in capsys.readouterr().out


def test_the_start_after_a_reset_deletes_the_previous_learners_memories_and_sessions(tmp_path):
    output = tmp_path / 'out'
    output.mkdir()
    (output / 'forget.json').write_text('{"owner": "learner-old"}')
    memory = Mock()
    memory.search_long_term_memory.side_effect = [
        SimpleNamespace(items=[SimpleNamespace(memory_id='m1'), SimpleNamespace(memory_id='m2')]), SimpleNamespace(items=[])]
    memory.list_sessions.return_value.items = [SimpleNamespace(session_id=s) for s in ['s1', 's2', 's3']]
    assert runtime.forget_previous_learner(output, memory) == 'Deleted 2 memories and 3 sessions of the previous learner.'
    memory.bulk_delete_long_term_memories.assert_called_once_with(memory_ids=['m1', 'm2'])
    assert memory.search_long_term_memory.call_args.kwargs['request']['filter_'] == {'owner_id': {'eq': 'learner-old'}}
    memory.list_sessions.assert_called_once_with(owner_id='learner-old')
    assert [c.kwargs['session_id'] for c in memory.delete_session_memory.call_args_list] == ['s1', 's2', 's3']
    assert not (output / 'forget.json').exists()
    assert runtime.forget_previous_learner(output, memory) is None  # nothing pending


def test_without_agent_memory_the_reset_note_is_kept_for_later(tmp_path):
    output = tmp_path / 'out'
    output.mkdir()
    (output / 'forget.json').write_text('{"owner": "learner-old"}')
    assert 'not configured' in runtime.forget_previous_learner(output, None)
    assert (output / 'forget.json').exists()


def test_ga_extraction_status_does_not_use_the_removed_preview_property_api():
    memory = fake_memory_with_bookmark(404)
    memory.sdk_configuration.globals.store_id = 'st_workshop'
    assert runtime.extraction_status(memory, 's1', 'e1') == 'not exposed by this service; check /memories'
    assert memory.requested == []
