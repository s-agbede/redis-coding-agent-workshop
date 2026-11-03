"""Slash-command suggestions as you type, using Redis's built-in autocomplete (FT.SUGADD / FT.SUGGET).

Typing "/" opens a menu of matching commands; the top match also appears as grey text ahead of
the cursor (press → to accept it, Tab to move through the menu). Every command starts with the
same score and each use adds one, so the commands you reach for most come first. Without Redis,
the plain command list is used; without a terminal (piped input), plain input() is used.
"""
from __future__ import annotations

from collections.abc import Callable, Iterator
import os
import sys
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggest
from prompt_toolkit.auto_suggest import Suggestion as GhostText
from prompt_toolkit.completion import Completer, Completion
from redis import Redis
from redis.commands.search.suggestion import Suggestion
from redis.exceptions import RedisError

KEY = 'workshop:commands'


class CommandSuggestions:
    """Command names ranked by use, kept in a Redis suggestion dictionary."""

    def __init__(self, client: Any, commands: dict[str, str]) -> None:
        self.client = client
        self.commands = commands
        if client is not None:
            # Seed once; later runs keep the scores your use has built up.
            known = {s.string for s in client.ft().sugget(KEY, '/', num=len(commands))} if client.exists(KEY) else set()
            missing = [Suggestion(name, 1.0) for name in commands if name not in known]
            if missing:
                client.ft().sugadd(KEY, *missing)

    def suggestions(self, prefix: str) -> list[str]:
        if self.client is None:
            return [name for name in self.commands if name.startswith(prefix)]
        return [s.string for s in self.client.ft().sugget(KEY, prefix, num=len(self.commands))]

    def used(self, command: str) -> None:
        if self.client is not None and command in self.commands:
            self.client.ft().sugadd(KEY, Suggestion(command, 1.0), increment=True)


def command_prefix(text: str) -> str | None:
    """The command being typed, or None once there's a space or it isn't a command."""
    return text if text.startswith('/') and ' ' not in text else None


class SlashMenu(Completer):
    def __init__(self, commands: CommandSuggestions) -> None:
        self.commands = commands

    def get_completions(self, document: Any, complete_event: Any) -> Iterator[Completion]:
        prefix = command_prefix(document.text_before_cursor)
        if prefix is None:
            return
        for name in self.commands.suggestions(prefix):
            yield Completion(name, start_position=-len(prefix), display_meta=self.commands.commands.get(name, ''))


class TopSuggestion(AutoSuggest):
    def __init__(self, commands: CommandSuggestions) -> None:
        self.commands = commands

    def get_suggestion(self, buffer: Any, document: Any) -> GhostText | None:
        prefix = command_prefix(document.text)
        top = self.commands.suggestions(prefix) if prefix else []
        return GhostText(top[0][len(prefix):]) if top and top[0] != prefix else None


def connect(commands: dict[str, str]) -> CommandSuggestions:
    """Suggestions backed by REDIS_URL, or by the built-in list if that Redis can't be reached."""
    url = os.environ.get('REDIS_URL', 'redis://localhost:6390/0')
    try:
        client = Redis.from_url(url, socket_timeout=2, decode_responses=True)
        client.ping()
        return CommandSuggestions(client, commands)
    except RedisError:
        print(f'Command suggestions: no Redis at {url}; using the built-in command list.')
        return CommandSuggestions(None, commands)


def prompt_reader(commands: CommandSuggestions) -> Callable[[str], str]:
    """A prompt with the suggestion menu in a terminal; plain input() for piped input."""
    if not sys.stdin.isatty():
        return input
    session: PromptSession[str] = PromptSession(
        completer=SlashMenu(commands), auto_suggest=TopSuggestion(commands), complete_while_typing=True)
    return session.prompt
