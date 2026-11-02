from unittest.mock import Mock

import pytest

pytest.importorskip("redis_agent_memory", reason="Install the optional iris dependency group")
from redis_agent_memory import AgentMemory, models
from tests.fakes import FakeClient, text
from experiments import iris_memory


def test_turn_records_original_user_and_actual_assistant_response():
    memory = Mock(spec=AgentMemory)
    client = FakeClient([text('I will use uv.')])
    assert hasattr(iris_memory, 'run_turn'), 'The memory-enabled turn is not implemented'
    answer = iris_memory.run_turn(client, memory, 'user-a', 'session-a', 'Use uv.', [])
    assert answer == 'I will use uv.'
    events = [call.kwargs for call in memory.add_session_event.call_args_list]
    assert [event['role'] for event in events] == [models.MessageRole.USER, models.MessageRole.ASSISTANT]
    assert [event['content'][0].text for event in events] == ['Use uv.', 'I will use uv.']
    assert all(event['session_id'] == 'session-a' for event in events)
    assert events[0]['actor_id'] == 'user-a'
    assert all(event['created_at'].tzinfo is not None for event in events)


def test_recall_filters_owner_and_type_on_server():
    memory = Mock(spec=AgentMemory)
    memory.search_long_term_memory.return_value.model_dump.return_value = {'items': []}
    assert hasattr(iris_memory, 'recall'), 'Scoped recall is not implemented'
    assert iris_memory.recall(memory, 'user-a', 'Python setup') == {'items': []}
    request = memory.search_long_term_memory.call_args.kwargs['request']
    assert request['filter_'] == {'owner_id': {'eq': 'user-a'}, 'memory_type': {'eq': 'user_preference'}}


def test_fresh_turn_receives_memories_without_old_conversation():
    memory = Mock(spec=AgentMemory)
    client = FakeClient([text('Use uv init.')])
    assert hasattr(iris_memory, 'run_turn'), 'The memory-enabled turn is not implemented'
    iris_memory.run_turn(client, memory, 'user-a', 'session-b', 'How do I start?', [{'text': 'Prefer uv'}])
    messages = client.calls[0]['messages']
    assert len(messages) == 2
    assert 'Prefer uv' in messages[0]['content']
    assert messages[1]['content'] == 'How do I start?'


def test_empty_model_answer_does_not_create_assistant_event():
    memory = Mock(spec=AgentMemory)
    client = FakeClient([text(None)])
    with pytest.raises(ValueError, match='no text response'):
        iris_memory.run_turn(client, memory, 'user-a', 'session-a', 'Use uv.', [])
    assert memory.add_session_event.call_count == 1
