"""Run agent.handle through the real loop, with the model and services mocked."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip('redis_agent_memory')
pytest.importorskip('redis_agent_playbook')
from openai.types.chat import ChatCompletionMessage
from context import PublishedSkill
from runtime import Workshop

ROOT = Path(__file__).resolve().parents[1]


def load_agent(capture: bool = False, recall: bool = False, playbook: bool = False):
    spec = importlib.util.spec_from_file_location('replay_agent', ROOT / 'agent.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.CAPTURE, module.RECALL, module.PLAYBOOK = capture, recall, playbook
    return module


def reply(message: ChatCompletionMessage) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def write_call(path: str, content: str) -> ChatCompletionMessage:
    return ChatCompletionMessage(role='assistant', content=None, tool_calls=[{
        'id': 'write-one', 'type': 'function',
        'function': {'name': 'write_file', 'arguments': json.dumps({'path': path, 'content': content})},
    }])


def scripted_model() -> Mock:
    client = Mock()
    client.chat.completions.create.side_effect = [
        reply(write_call('sample.py', 'def f() -> None: ...\n')),
        reply(ChatCompletionMessage(role='assistant', content='Created the sample.')),
    ]
    return client


@pytest.mark.parametrize('capture,recall,playbook', [
    (False, False, False), (True, False, False), (True, True, False), (True, True, True),
])
def test_each_flag_switches_on_only_its_own_step(tmp_path, capture, recall, playbook):
    (tmp_path / 'AGENTS.md').write_text('Use type hints.')
    memory, published = Mock(), Mock()
    memory.search_long_term_memory.return_value.items = [SimpleNamespace(text='Prefers Google-style docstrings.')]
    published.retrieve.return_value = PublishedSkill(name='report-validation', version=2, instructions='Use Decimal.')
    app = Workshop(load_agent(capture, recall, playbook), scripted_model(), memory, published, 'learner', tmp_path, tmp_path / 'out')
    assert app.turn('Create a sample') == 'Created the sample.'
    assert (tmp_path / 'sample.py').is_file()
    assert memory.add_session_event.call_count == (2 if capture else 0)
    if capture:
        first, second = (call.kwargs for call in memory.add_session_event.call_args_list)
        assert (first['actor_id'], first['content'][0].text) == ('learner', 'Create a sample')
        assert second['content'][0].text == 'Created the sample.'
    assert memory.search_long_term_memory.called == recall
    if recall:
        assert memory.search_long_term_memory.call_args.kwargs['request']['filter_'] == {
            'owner_id': {'eq': 'learner'}, 'memory_type': {'eq': 'coding_preference'}}
    assert published.retrieve.called == playbook
    if playbook:
        assert published.retrieve.call_args.kwargs == {'min_score': 0.7}
    request = str(app.state.last_request)
    assert 'Use type hints.' in request
    assert ('Prefers Google-style docstrings.' in request) == recall
    assert ('report-validation, version 2' in request) == playbook


def test_the_session_keeps_the_conversation_but_not_the_recalled_context(tmp_path):
    memory = Mock()
    memory.search_long_term_memory.return_value.items = [SimpleNamespace(text='Prefers Google-style docstrings.')]
    app = Workshop(load_agent(recall=True), scripted_model(), memory, None, 'learner', tmp_path, tmp_path / 'out')
    app.turn('Create a sample')
    assert app.state.history[0] == {'role': 'user', 'content': 'Create a sample'}
    assert 'Google-style' not in str(app.state.history)


def test_agent_edits_agents_md_and_a_new_session_reloads_it(tmp_path):
    instructions = tmp_path / 'AGENTS.md'
    instructions.write_text('Use type hints.\n')
    edited = 'Use type hints.\nWe target Python 3.12.\n'
    client = Mock()
    client.chat.completions.create.side_effect = [
        reply(write_call('AGENTS.md', edited)),
        reply(ChatCompletionMessage(role='assistant', content='Added it.')),
    ]
    app = Workshop(load_agent(), client, None, None, 'learner', tmp_path, tmp_path / 'out')
    app.turn('Add a note to AGENTS.md that we target Python 3.12.')
    assert instructions.read_text() == edited
    assert '3.12' not in app.state.instructions  # Reloaded at the session boundary, not mid-session.
    app.command('/new-session')
    assert app.state.instructions == edited and app.state.history == []


def test_a_capability_without_its_service_names_the_missing_setting(tmp_path):
    app = Workshop(load_agent(capture=True), scripted_model(), None, None, 'learner', tmp_path, tmp_path / 'out')
    with pytest.raises(ValueError, match='AGENT_MEMORY'):
        app.turn('Create a sample')
