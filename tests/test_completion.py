"""Slash-command suggestions: they come from Redis, ranked by use, and appear as you type."""
from prompt_toolkit.document import Document

import completion

COMMANDS = {'/status': 'Owner, session and capabilities', '/sessions': 'Your stored sessions',
            '/skills': 'The team procedure', '/view-context': 'What was sent to the model'}


class FakeSuggestions:
    """Stands in for redis-py's FT.SUGADD / FT.SUGGET: prefix match, highest score first."""

    def __init__(self):
        self.scores = {}

    def sugadd(self, key, *suggestions, increment=False):
        for suggestion in suggestions:
            current = self.scores.get(suggestion.string, 0) if increment else 0
            self.scores[suggestion.string] = current + suggestion.score

    def sugget(self, key, prefix, num=10):
        matches = sorted((s for s in self.scores if s.startswith(prefix)), key=lambda s: -self.scores[s])
        return [type('Suggestion', (), {'string': s})() for s in matches[:num]]


class FakeRedis:
    def __init__(self):
        self.index = FakeSuggestions()

    def ft(self):
        return self.index

    def exists(self, key):
        return int(bool(self.index.scores))


def test_suggestions_match_the_typed_prefix():
    commands = completion.CommandSuggestions(FakeRedis(), COMMANDS)
    assert sorted(commands.suggestions('/s')) == ['/sessions', '/skills', '/status']
    assert commands.suggestions('/v') == ['/view-context']


def test_commands_you_use_most_come_first():
    commands = completion.CommandSuggestions(FakeRedis(), COMMANDS)
    for _ in range(3):
        commands.used('/skills')
    assert commands.suggestions('/s')[0] == '/skills'


def test_the_menu_lists_matches_with_descriptions_while_typing():
    menu = completion.SlashMenu(completion.CommandSuggestions(FakeRedis(), COMMANDS))
    items = list(menu.get_completions(Document('/st'), None))
    assert [(item.text, item.display_meta_text) for item in items] == [('/status', 'Owner, session and capabilities')]
    assert list(menu.get_completions(Document('write a function'), None)) == []
    assert list(menu.get_completions(Document('/resume abc'), None)) == []


def test_ghost_text_shows_the_rest_of_the_top_suggestion():
    ghost = completion.TopSuggestion(completion.CommandSuggestions(FakeRedis(), COMMANDS))
    assert ghost.get_suggestion(None, Document('/vie')).text == 'w-context'
    assert ghost.get_suggestion(None, Document('/view-context')) is None
    assert ghost.get_suggestion(None, Document('hello')) is None


def test_without_redis_the_built_in_list_still_suggests():
    commands = completion.CommandSuggestions(None, COMMANDS)
    assert sorted(commands.suggestions('/s')) == ['/sessions', '/skills', '/status']
    commands.used('/status')  # no error without Redis
