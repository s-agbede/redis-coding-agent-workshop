"""Session commands and request assembly for the memory workshop."""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Iterator
from uuid import uuid4

from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field
from redis_agent_memory import AgentMemory, errors

import tools
import ui
from playbook import PlaybookStore

# Slash commands and the description shown beside each in the suggestion menu.
COMMANDS = {
    '/status': 'Owner, session and what is switched on',
    '/view-context': 'Exactly what was sent to the model last',
    '/new-session': 'Start a fresh conversation',
    '/sessions': 'Your stored sessions',
    '/resume': 'Bring a stored session back: /resume <number>',
    '/events': 'What Agent Memory stored for this session',
    '/memories': 'What Agent Memory learned about you',
    '/forget': 'Forget one of your memories: /forget <id>',
    '/skills': 'The team skills published in Agent Playbook',
    '/publish-skill': 'Publish the team skill (instructor)',
    '/help': 'List the commands',
}
HELP = (
    '/status  /view-context  /new-session  /sessions  /resume <number>\n'
    '/events  /memories  /forget <id>  /skills  /publish-skill (instructor)  /help  exit'
)


# After each extraction run, Agent Memory records on the session the last event it extracted
# for each memory type. It is an internal marker, not a documented API, so treat it as a hint.
EXTRACTION_BOOKMARK = 'custom_extracted_up_to_event_id_coding_preference'


def extraction_status(memory: Any, session_id: str, last_event_id: str) -> str:
    """'up to date' once extraction has reached the session's last event, otherwise 'pending'."""
    config = memory.sdk_configuration
    if str(config.globals.store_id).startswith('st_'):
        # The GA API does not expose the Preview service's internal bookmark.
        return 'not exposed by this service; check /memories'
    url = (f'{config.server_url}/v1/stores/{config.globals.store_id}/session-memory/'
           f'{session_id}/properties/{EXTRACTION_BOOKMARK}')
    response = config.client.get(url, headers={'Authorization': f'Bearer {config.security.api_key}'})
    if response.status_code == 404:
        return 'pending'  # not extracted yet
    if response.status_code != 200:
        raise RuntimeError(f'Could not read extraction status: HTTP {response.status_code}')
    return 'up to date' if response.json().get('value') == last_event_id else 'pending'


def forget_previous_learner(output: Path, memory: Any) -> str | None:
    """After a workshop reset, delete the previous learner's memories and sessions from Agent Memory.

    The reset records the old owner in output/forget.json; this runs on the next start, where
    the Agent Memory connection exists. Only that owner's data is touched.
    """
    note = output / 'forget.json'
    if not note.exists():
        return None
    if memory is None:
        return "The previous learner's memories were not deleted: Agent Memory is not configured."
    owner = json.loads(note.read_text())['owner']
    deleted = 0
    while True:  # search returns a page at a time; repeat until nothing is left
        found = memory.search_long_term_memory(request={'filter_': {'owner_id': {'eq': owner}}, 'limit': 100})
        ids = [item.memory_id for item in found.items]
        if not ids:
            break
        memory.bulk_delete_long_term_memories(memory_ids=ids)
        deleted += len(ids)
    sessions = [item.session_id for item in memory.list_sessions(owner_id=owner).items]
    for session_id in sessions:
        memory.delete_session_memory(session_id=session_id)
    note.unlink()
    return f'Deleted {deleted} memories and {len(sessions)} sessions of the previous learner.'


class Session(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    owner: str
    project: Path
    session_id: str = Field(default_factory=lambda: uuid4().hex)
    instructions: str
    history: list[Any] = Field(default_factory=list)
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


class Services:
    """What agent.handle needs from the runtime: the model, Agent Memory, Playbook and the project's tools."""

    def __init__(self, client: OpenAI, memory: AgentMemory | None, playbook: PlaybookStore | None,
                 tools: dict[str, Callable[..., str]], on_request: Callable[[list[Any]], None]) -> None:
        self.client, self.tools, self.on_request = client, tools, on_request
        self._memory, self._playbook = memory, playbook

    @property
    def memory(self) -> AgentMemory:
        if self._memory is None:
            raise ValueError('Redis Agent Memory is not configured. Add the AGENT_MEMORY_* settings to .env.')
        return self._memory

    @property
    def playbook(self) -> PlaybookStore:
        if self._playbook is None:
            raise ValueError('Redis Agent Playbook is not configured. Add the PLAYBOOK_* settings to .env.')
        return self._playbook


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
        print(f'Capture:  {on[self.learner.CAPTURE]}   Recall: {on[self.learner.RECALL]}'
              f'   Playbook: {on[self.learner.PLAYBOOK]}')
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

    def session_events(self, session_id: str) -> list[dict[str, Any]] | None:
        """The session's stored events, or None when Agent Memory has no such session.

        Agent Memory creates a session with its first event, so a session that ran with
        CAPTURE off does not exist there yet.
        """
        try:
            session = self.memory_client().get_session_memory(session_id=session_id)
        except errors.NotFoundErrorResponseContent:
            return None
        return session.model_dump(mode='json', by_alias=True)['events']

    def stored_sessions(self) -> list[str]:
        return [item.session_id for item in self.memory_client().list_sessions(owner_id=self.state.owner).items]

    def find_session(self, reference: str) -> str:
        """A stored session, by its number in /sessions or by the start of its ID."""
        sessions = self.stored_sessions()
        if reference.isdigit() and 1 <= int(reference) <= len(sessions):
            return sessions[int(reference) - 1]
        matches = [session_id for session_id in sessions if session_id.startswith(reference)]
        if len(matches) == 1:
            return matches[0]
        problem = 'matches more than one session' if matches else 'not found'
        raise ValueError(f'No stored session {reference} ({problem}). /sessions lists them; use its number.')

    def resume(self, reference: str) -> None:
        session_id = self.find_session(reference)
        events = self.session_events(session_id)
        if events is None:
            raise ValueError(f'No stored session {reference}. /sessions lists the ones Agent Memory has.')
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
            sessions = self.stored_sessions()
            for number, session_id in enumerate(sessions, start=1):
                # Label each session by its first message, so you can tell them apart.
                first = next((event for event in self.session_events(session_id) or [] if event['role'] == 'USER'), None)
                label = ' '.join(part.get('text', '') for part in first['content'])[:60] if first else '(no messages)'
                current = '   (current)' if session_id == self.state.session_id else ''
                print(f'{number}  {session_id[:8]}  {label}{current}')
            if sessions:
                print('\n/resume <number> brings one back.')
            else:
                print('No stored sessions yet. Capture must be on for sessions to be stored.')
        elif name == '/resume':
            if not argument:
                raise ValueError('Usage: /resume <number>, from the list /sessions shows.')
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
            events = self.session_events(self.state.session_id)
            if events is None:
                print('Nothing recorded for this session yet. Turn on CAPTURE (Section 3) and send a message.')
                return
            for event in events:
                text = ' '.join(part.get('text', '') for part in event['content'])
                print(f'{event["role"]} ({event.get("actorId", "?")}): {text[:150]}')
            if not events:
                print('No events stored for this session.')
                return
            status = extraction_status(self.memory_client(), self.state.session_id, events[-1]['eventId'])
            print(f'\nExtraction: {status}' + (' (runs within about a minute of the last message)' if status == 'pending' else ''))
        elif name == '/memories':
            items = self.memory_client().search_long_term_memory(request={
                'filter_': {'owner_id': {'eq': self.state.owner}},
                'limit': 50,
            }).model_dump(mode='json', by_alias=True)['items']
            for item in items:
                print(f'- [{item["memoryId"][:8]}] {item["text"]} ({item.get("memoryType", "?")})')
            if not items:
                print('Nothing extracted yet. Extraction runs in the background; try again shortly.')
        elif name == '/forget':
            if not argument:
                raise ValueError('Usage: /forget <id>. /memories shows each memory with its id.')
            items = self.memory_client().search_long_term_memory(request={
                'filter_': {'owner_id': {'eq': self.state.owner}}, 'limit': 50,
            }).model_dump(mode='json', by_alias=True)['items']
            match = next((item for item in items if item['memoryId'].startswith(argument.strip())), None)
            if match is None:
                raise ValueError(f'No memory of yours starts with {argument.strip()}. /memories lists them.')
            self.memory_client().bulk_delete_long_term_memories(memory_ids=[match['memoryId']])
            print(f'Forgot: {match["text"]}')
        elif name == '/publish-skill':
            entry_id, version = self.playbook_store().publish(Path(__file__).resolve().parent / 'skills/report-validation')
            print(f'Published report-validation as entry {entry_id}, version {version}.')
        elif name == '/skills':
            skills = self.playbook_store().published_skills()
            for skill in skills:
                summary = next((line for line in skill.instructions.splitlines() if line.startswith('- ')), '')
                print(f'{skill.name}, version {skill.version}  {summary[2:90]}')
            print('\nThe agent uses the one that fits the task.' if skills else 'No published team skills yet.')
        elif name == '/help':
            print(HELP)
        else:
            print('Unknown command. /help lists them.')

    def snapshot_request(self, messages: list[Any]) -> None:
        self.state.last_request = serialized(messages)

    def turn(self, prompt: str) -> str | None:
        self.state.last_request = []
        services = Services(self.client, self.memory, self.playbook, self.registry, self.snapshot_request)
        answer = self.learner.handle(prompt, self.state, services)
        if answer:
            ui.show_answer(answer)
        return answer
