"""Replay the real learner loop with deterministic external-service responses."""
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


@pytest.mark.parametrize('path,capture,recall,playbook', [
    ('agent.py', False, False, False),
    ('solutions/steps/01-capture.py', True, False, False),
    ('solutions/steps/02-recall.py', True, True, False),
    ('solutions/steps/03-playbook.py', True, True, True),
])
def test_each_stage_runs_tool_loop_with_only_enabled_capabilities(tmp_path, path, capture, recall, playbook):
    learner = load_agent(path)
    project = tmp_path / 'project'; project.mkdir()
    (project / 'AGENTS.md').write_text('Use uv.')
    memory, published, client = Mock(), Mock(), Mock()
    memory.search_long_term_memory.return_value.model_dump.return_value = {
        'items': [{'text': 'Add explanatory comments', 'owner_id': 'learner'}],
    }
    published.retrieve.return_value = PublishedSkill(
        source='playbook://service/skills/own/versions/3', version=3,
        instructions='Validate every row', digest='abc',
    )
    tool_response = ChatCompletionMessage(role='assistant', content=None, tool_calls=[{
        'id': 'write-one', 'type': 'function',
        'function': {'name': 'write_file', 'arguments': json.dumps({'path': 'sample.py', 'content': '# Explain a check\n'})},
    }])
    answer = ChatCompletionMessage(role='assistant', content='Created the sample.')
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=tool_response)]),
        SimpleNamespace(choices=[SimpleNamespace(message=answer)]),
    ]
    app = Workshop(learner, client, memory, published, 'learner', project, tmp_path/'output')
    assert app.turn('Create a sample') == 'Created the sample.'
    assert (project/'sample.py').read_text() == '# Explain a check\n'
    assert len(app.state.last_request) >= 3
    assert app.state.last_request[-1]['role'] == 'tool'
    assert all(message.get('role') != 'system' for message in __import__('runtime', fromlist=['serialized']).serialized(app.state.history))
    assert memory.add_session_event.call_count == (2 if capture else 0)
    if capture:
        events = memory.add_session_event.call_args_list
        assert events[0].kwargs['content'][0].text == 'Create a sample'
        assert events[1].kwargs['content'][0].text == 'Created the sample.'
        assert events[0].kwargs['actor_id'] == 'learner'
    assert memory.search_long_term_memory.called == recall
    if recall:
        request = memory.search_long_term_memory.call_args.kwargs['request']
        assert request['filter_'] == {'owner_id': {'eq': 'learner'}, 'memory_type': {'eq': 'user_preference'}}
    assert published.retrieve.called == playbook
    old_session = app.state.session_id
    app.command('/new-session')
    assert app.state.session_id != old_session and app.state.owner == 'learner'
    assert not app.state.history and not app.state.last_request and app.state.skill is None


def test_checker_rejects_empty_validator_and_accepts_reference(tmp_path, capsys):
    learner = load_agent('agent.py')
    app = Workshop(learner, Mock(), None, None, 'learner', tmp_path, tmp_path/'out')
    target = tmp_path/'validator.py'
    target.write_text('def validate_report(rows):\n    return []\n')
    app.command('/verify')
    assert 'Independent checker exit: 1' in capsys.readouterr().out
    target.write_text((ROOT/'solutions/validator.py').read_text())
    app.command('/verify')
    assert 'Independent checker exit: 0' in capsys.readouterr().out


def test_assistant_capture_failure_preserves_completed_work_and_evidence(tmp_path, capsys):
    learner = load_agent('solutions/steps/01-capture.py')
    client, memory = Mock(), Mock()
    client.chat.completions.create.return_value = SimpleNamespace(choices=[SimpleNamespace(
        message=ChatCompletionMessage(role='assistant', content='Actual completed answer'),
    )])
    memory.add_session_event.side_effect = [None, RuntimeError('capture unavailable')]
    app = Workshop(learner, client, memory, None, 'owner', tmp_path, tmp_path/'output')
    with pytest.raises(RuntimeError, match='capture unavailable'):
        app.turn('Do a task')
    assert 'Actual completed answer' in capsys.readouterr().out
    reports = list((tmp_path/'output').glob('*.json'))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    assert report['answer'] == 'Actual completed answer'
    assert report['error_type'] == 'RuntimeError'
    assert len(app.state.history) == 2


def test_agent_edits_project_instruction_and_new_session_reloads_it(tmp_path):
    learner = load_agent('agent.py')
    instructions = tmp_path / 'AGENTS.md'
    instructions.write_text('Preserve the validator interface.\n')
    client = Mock()
    edited = 'Preserve the validator interface.\nUse uv for Python projects.\n'
    client.chat.completions.create.side_effect = [
        SimpleNamespace(choices=[SimpleNamespace(message=ChatCompletionMessage(
            role='assistant', content=None, tool_calls=[{
                'id': 'edit-instructions', 'type': 'function', 'function': {
                    'name': 'write_file', 'arguments': json.dumps({'path': 'AGENTS.md', 'content': edited}),
                },
            }],
        ))]),
        SimpleNamespace(choices=[SimpleNamespace(message=ChatCompletionMessage(role='assistant', content='Updated project instructions.'))]),
    ]
    app = Workshop(learner, client, None, None, 'learner', tmp_path, tmp_path/'output')
    app.state.history = [{'role': 'user', 'content': 'Always add explanatory comments.'}]
    app.turn('Add Use uv for Python projects to AGENTS.md and preserve its contents.')
    assert instructions.read_text() == edited
    assert 'Use uv' not in app.state.instructions  # Reload is explicit, at the session boundary.
    app.command('/new-session')
    assert app.state.instructions == edited
    assert app.state.history == []
    assert 'explanatory comments' not in app.state.instructions
