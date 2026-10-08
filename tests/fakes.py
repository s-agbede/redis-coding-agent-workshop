"""A fake OpenAI-shaped client for driving run_agent deterministically in tests.

It mimics just the surface run_agent touches:
    client.chat.completions.create(model=..., messages=..., tools=...)
        -> response.choices[0].message  with .content and .tool_calls

Each fake message's .tool_calls entries expose .id and .function.{name,arguments},
matching the real SDK shape. The client replays a scripted queue of responses and
records every create() call so tests can assert how the loop drove the model.
"""

import json
from copy import deepcopy


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        # The real SDK delivers arguments as a JSON string.
        self.arguments = arguments if isinstance(arguments, str) else json.dumps(arguments)


class FakeToolCall:
    def __init__(self, id, name, arguments):
        self.id = id
        self.type = "function"
        self.function = FakeFunction(name, arguments)


class FakeMessage:
    def __init__(self, content=None, tool_calls=None):
        self.role = "assistant"
        self.content = content
        self.tool_calls = tool_calls  # None or a list of FakeToolCall


class _Choice:
    def __init__(self, message):
        self.message = message


class _Response:
    def __init__(self, message):
        self.choices = [_Choice(message)]


class _Completions:
    def __init__(self, scripted):
        self._queue = list(scripted)
        self.calls = []  # kwargs of each create() call, in order

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if not self._queue:
            raise AssertionError("FakeClient ran out of scripted responses")
        return _Response(self._queue.pop(0))


class _Chat:
    def __init__(self, scripted):
        self.completions = _Completions(scripted)


class FakeClient:
    """Replays `scripted` (a list of FakeMessage) across successive create() calls."""

    def __init__(self, scripted):
        self.chat = _Chat(scripted)

    @property
    def calls(self):
        return self.chat.completions.calls


def text(content):
    """A model turn that returns a final text answer (no tools)."""
    return FakeMessage(content=content)


def tool_turn(*calls):
    """A model turn that requests one or more tools.

    Each call is (id, name, arguments) where arguments is a dict or JSON string.
    """
    return FakeMessage(
        content=None,
        tool_calls=[FakeToolCall(cid, name, args) for cid, name, args in calls],
    )
