"""Run each stage's learner agent through the real loop, with the services mocked."""
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


def load_agent(path: str):
    spec = importlib.util.spec_from_file_location('replay_agent', ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reply(message: ChatCompletionMessage) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def write_call(path: str, content: str) -> ChatCompletionMessage:
    return ChatCompletionMessage(role='assistant', content=None, tool_calls=[{
        'id': 'write-one', 'type': 'function',
        'function': {'name': 'write_file', 'arguments': json.dumps({'path': path, 'content': content})},
    }])


@pytest.mark.parametrize('path,capture,recall,playbook', [
    ('agent.py', False, False, False),
    ('solutions/steps/01-capture.py', True, False, False),
    ('solutions/steps/02-recall.py', True, True, False),
    ('solutions/steps/03-playbook.py', True, True, True),
])
def test_each_stage_uses_only_its_enabled_capabilities(tmp_path, path, capture, recall, playbook):
    learner = load_agent(path)
    (tmp_path / 'AGENTS.md').write_text('Use type hints.')
    memory, published, client = Mock(), Mock(), Mock()
    memory.search_long_term_memory.return_value.model_dump.return_value = {
        'items': [{'text': 'The user prefers Google-style docstrings.'}],
    }
    published.retrieve.return_value = PublishedSkill(name='report-validation', version=2, instructions='Use Decimal.')
    client.chat.completions.create.side_effect = [
        reply(write_call('sample.py', 'def f() -> None: ...\n')),
        reply(ChatCompletionMessage(role='assistant', content='Created the sample.')),
    ]
    app = Workshop(learner, client, memory, published, 'learner', tmp_path, tmp_path / 'out')
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
    request = app.state.last_request
    assert ('Google-style docstrings' in request[1]['content']) == recall
    assert ('report-validation, version 2' in str(request)) == playbook


def test_agent_edits_agents_md_and_a_new_session_reloads_it(tmp_path):
    learner = load_agent('agent.py')
    instructions = tmp_path / 'AGENTS.md'
    instructions.write_text('Use type hints.\n')
    edited = 'Use type hints.\nWe target Python 3.12.\n'
    client = Mock()
    client.chat.completions.create.side_effect = [
        reply(write_call('AGENTS.md', edited)),
        reply(ChatCompletionMessage(role='assistant', content='Added it.')),
    ]
    app = Workshop(learner, client, None, None, 'learner', tmp_path, tmp_path / 'out')
    app.turn('Add a note to AGENTS.md that we target Python 3.12.')
    assert instructions.read_text() == edited
    assert '3.12' not in app.state.instructions  # Reloaded at the session boundary, not mid-session.
    app.command('/new-session')
    assert app.state.instructions == edited and app.state.history == []
