"""Session commands and request assembly for the memory workshop."""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType
from typing import Any, Callable, Iterator
from uuid import uuid4

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from redis_agent_memory import AgentMemory, models

import tools
import ui
from context import PublishedSkill
from playbook import PlaybookStore

SYSTEM = 'You are a coding assistant working in this project. Use your tools to read and change files.'
HELP = (
    '/status  /view-context  /new-session  /sessions  /resume <id>\n'
    '/events  /memories  /skills  /publish-skill (instructor)  /verify  /help  exit'
)


class Session(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    owner: str
    project: Path
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    instructions: str
    history: list[Any] = Field(default_factory=list)
    preferences: list[dict[str, Any]] = Field(default_factory=list)
    skill: PublishedSkill | None = None
    last_request: list[dict[str, Any]] = Field(default_factory=list)

    @classmethod
    def start(cls, owner: str, project: Path, session_id: str | None = None) -> Session:
        path = project.resolve()
        file = path / 'AGENTS.md'
        instructions = file.read_text(encoding='utf-8') if file.is_file() else ''
        return cls(owner=owner, project=path, instructions=instructions,
                   **({'session_id': session_id} if session_id else {}))


def serialized(messages: list[Any]) -> list[dict[str, Any]]:
    return [
        dict(message) if isinstance(message, dict) else message.model_dump(mode='json', exclude_none=True)
        for message in messages
    ]


def compose(state: Session, learner: ModuleType, prompt: str) -> list[Any]:
    system = SYSTEM + ('\n\nProject instructions (AGENTS.md):\n' + state.instructions if state.instructions else '')
    messages: list[Any] = [{'role': 'system', 'content': system}]
    # Recalled context is rebuilt for every task, so stale results never pile up in history.
    extra = [
        learner.preference_context(state.preferences) if state.preferences else '',
        learner.skill_context(state.skill) if state.skill else '',
    ]
    if any(extra):
        messages.append({'role': 'system', 'content': '\n\n'.join(part for part in extra if part)})
    return messages + list(state.history) + [{'role': 'user', 'content': prompt}]


def describe(message: dict[str, Any]) -> str:
    """One readable line (or block) per message for /view-context."""
    role = message.get('role', '?')
    if message.get('tool_calls'):
        names = ', '.join(call['function']['name'] for call in message['tool_calls'])
        return f'{role}: (asks to run {names})'
    content = message.get('content') or ''
    if role == 'tool' and len(content) > 300:
        content = content[:300] + ' …'
    return f'{role}: {content}'


@contextmanager
def working_directory(project: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(project)
    try:
        yield
    finally:
        os.chdir(previous)


def project_tools(project: Path) -> dict[str, Callable[..., str]]:
    """File tools bound to the project; shell commands still require approval."""
    root = project.resolve()

    def resolve(path: str) -> Path:
        result = (root / path).resolve()
        if not result.is_relative_to(root):
            raise ValueError('File access outside the project is not allowed')
        return result

    def read_file(path: str, offset: int = 1, limit: int = 80) -> str:
        return tools.file_excerpt(resolve(path).read_text(encoding='utf-8'), offset, limit)

    def list_files(path: str = '.') -> str:
        target = resolve(path)
        if not target.is_dir():
            raise ValueError('Expected a project directory')
        names = [str(p.relative_to(root)) for p in sorted(target.rglob('*'))
                 if p.is_file() and not p.is_symlink() and not any(x in tools._SKIP_DIRS for x in p.parts)]
        return '\n'.join(names[:200])[:tools.MAX_OUTPUT_CHARS] or '(no files found)'

    def write_file(path: str, content: str) -> str:
        return tools.write_file(str(resolve(path)), content)

    def str_replace(path: str, old_str: str, new_str: str) -> str:
        return tools.str_replace(str(resolve(path)), old_str, new_str)

    def run_bash(command: str, timeout: int = 60) -> str:
        with working_directory(root):
            return tools.run_bash(command, timeout)

    return dict(read_file=read_file, list_files=list_files, write_file=write_file,
                str_replace=str_replace, run_bash=run_bash)


class Workshop:
    def __init__(self, learner: ModuleType, client: OpenAI, memory: AgentMemory | None,
                 playbook: PlaybookStore | None, owner: str, project: Path, output: Path) -> None:
        self.learner = learner
        self.client = client
        self.memory = memory
        self.playbook = playbook
        self.state = Session.start(owner, project)
        self.output = output
        self.registry = project_tools(project)

    def memory_client(self) -> AgentMemory:
        if self.memory is None:
            raise ValueError('Redis Agent Memory is not configured. Add the AGENT_MEMORY_* settings to .env.')
        return self.memory

    def playbook_store(self) -> PlaybookStore:
        if self.playbook is None:
            raise ValueError('Redis Agent Playbook is not configured. Add the PLAYBOOK_* settings to .env.')
        return self.playbook

    def status(self) -> None:
        on = {True: 'on', False: 'off'}
        print(f'Owner:    {self.state.owner}')
        print(f'Session:  {self.state.session_id}')
        print(f'Capture:  {on[self.learner.CAPTURE_ENABLED]}   Recall: {on[self.learner.RECALL_ENABLED]}'
              f'   Playbook: {on[self.learner.PLAYBOOK_ENABLED]}')
        print(f'Memory:   {"configured" if self.memory else "not configured"}')
        playbook = 'not configured'
        if self.playbook:
            playbook = f'configured, team skill {self.playbook.skill_id or "from your own /publish-skill"}'
        print(f'Playbook: {playbook}')

    def new_session(self, session_id: str | None = None, history: list[Any] | None = None) -> None:
        self.state = Session.start(self.state.owner, self.state.project, session_id)
        self.state.history = history or []
        ui.console.clear()
        if session_id is None:
            ui.info(f'New session {self.state.session_id}. Conversation cleared; AGENTS.md reloaded.')
        else:
            ui.info(f'Resumed session {session_id}.')

    def resume(self, session_id: str) -> None:
        events = self.memory_client().get_session_memory(session_id=session_id).model_dump(
            mode='json', by_alias=True,
        )['events']
        history = [
            {'role': event['role'].lower(), 'content': ' '.join(part.get('text', '') for part in event['content'])}
            for event in events
        ]
        self.new_session(session_id, history)
        for message in history:
            print(describe(message)[:200])
        ui.info(f'Resumed {len(history)} messages from Redis Agent Memory.')

    def command(self, command: str) -> None:
        name, _, argument = command.partition(' ')
        if name == '/status':
            self.status()
        elif name == '/new-session':
            self.new_session()
        elif name == '/sessions':
            sessions = self.memory_client().list_sessions(filter_owner_id=self.state.owner).items
            for session_id in sessions:
                print(session_id + ('   (current)' if session_id == self.state.session_id else ''))
            if not sessions:
                print('No stored sessions yet. Capture must be on for sessions to be stored.')
        elif name == '/resume':
            if not argument:
                raise ValueError('Usage: /resume <session id>. /sessions lists them.')
            self.resume(argument.strip())
        elif name == '/view-context':
            if not self.state.last_request:
                print(f'Nothing sent to the model yet in this session. AGENTS.md is loaded; '
                      f'{len(self.state.history)} conversation messages so far.')
            else:
                print(f'Latest request sent to the model ({len(self.state.last_request)} messages):\n')
                for number, message in enumerate(self.state.last_request, start=1):
                    print(f'[{number}] {describe(message)}\n')
        elif name == '/events':
            events = self.memory_client().get_session_memory(session_id=self.state.session_id).model_dump(
                mode='json', by_alias=True,
            )['events']
            for event in events:
                text = ' '.join(part.get('text', '') for part in event['content'])
                print(f'{event["role"]} ({event.get("actorId", "?")}): {text[:150]}')
            if not events:
                print('No events stored for this session.')
        elif name == '/memories':
            items = self.memory_client().search_long_term_memory(request={
                'filter_': {'owner_id': {'eq': self.state.owner}},
                'limit': 50,
            }).model_dump(mode='json', by_alias=True)['items']
            for item in items:
                print(f'- {item["text"]} ({item.get("memoryType", "?")})')
            if not items:
                print('Nothing extracted yet. Extraction runs in the background; try again shortly.')
        elif name == '/publish-skill':
            entry_id, version = self.playbook_store().publish(Path(__file__).resolve().parent / 'skills/report-validation')
            print(f'Published report-validation as entry {entry_id}, version {version}.')
        elif name == '/skills':
            skill = self.playbook_store().retrieve('Validate the rows of an incoming report')
            if skill is None:
                print('No published team skill found.')
            else:
                print(f'{skill.name}, version {skill.version}\n\n{skill.instructions}')
        elif name == '/verify':
            result = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
                                    cwd=self.state.project, text=True, capture_output=True, timeout=60)
            print(result.stdout + result.stderr)
            print('Tests passed.' if result.returncode == 0 else 'Tests failed.')
        elif name == '/help':
            print(HELP)
        else:
            print('Unknown command. /help lists them.')

    def snapshot_request(self, messages: list[Any]) -> None:
        self.state.last_request = serialized(messages)

    def turn(self, prompt: str) -> str | None:
        learner, state = self.learner, self.state
        state.preferences, state.skill, state.last_request = [], None, []
        if learner.CAPTURE_ENABLED:
            learner.record_event(self.memory_client(), state.session_id, state.owner, models.MessageRole.USER, prompt)
        if learner.RECALL_ENABLED:
            state.preferences = learner.recall_preferences(self.memory_client(), state.owner, prompt)
            ui.info('Recalled: ' + ('; '.join(item['text'] for item in state.preferences) or 'nothing'))
        if learner.PLAYBOOK_ENABLED:
            state.skill = self.playbook_store().retrieve(prompt)
            ui.info(f'Team procedure: {state.skill.name}, version {state.skill.version}' if state.skill
                    else 'Team procedure: none for this task')
        messages = compose(state, learner, prompt)
        context_size = len(messages) - len(state.history) - 1
        try:
            learner.run_agent(self.client, messages, learner.TOOL_SCHEMAS, self.registry,
                              max_iters=int(os.environ.get('AGENT_MAX_ITERS', '25')), on_request=self.snapshot_request)
        finally:
            state.history = messages[context_size:]
        answer = getattr(messages[-1], 'content', None)
        if answer:
            ui.show_answer(answer)
            if learner.CAPTURE_ENABLED:
                learner.record_event(self.memory_client(), state.session_id, 'coding-assistant',
                                     models.MessageRole.ASSISTANT, answer)
        return answer
