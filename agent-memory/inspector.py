"""Agent Memory inspector: this workspace's sessions, long-term memories and store settings.

Serves one page at /memory/ and a few JSON routes under /memory/api/. Sessions and memories
come from the Agent Memory data plane, scoped to the workspace's owner. Store settings come
from the Control Plane, which is only available when Agent Memory is self-hosted.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from redis_agent_memory import AgentMemory

WORKSPACE = Path(os.environ.get('WORKSPACE_ROOT', '/workspace'))
PAGE = Path(__file__).with_name('inspector.html').read_bytes()
# Only these store settings are shown; connection details and credentials never leave the server.
SETTINGS = ('name', 'shortMemory', 'longTermMemory', 'extractionStrategy', 'extractionCadence',
            'summarization', 'customMemoryTypes', 'longTermMemoryExclusions')


def read_setting(name: str) -> str:
    """An environment value, or the contents of the file named by NAME_FILE."""
    value = os.environ.get(name, '').strip()
    path = os.environ.get(f'{name}_FILE', '').strip()
    if not value and path and Path(path).is_file():
        value = Path(path).read_text().strip()
    return value


def owner() -> str:
    explicit = os.environ.get('IRIS_OWNER_ID', '').strip()
    if explicit:
        return explicit
    identity = WORKSPACE / 'output/workshop/owner.json'
    if not identity.is_file():
        raise LookupError('Start the agent once in the terminal; it creates your owner ID.')
    return json.loads(identity.read_text())['owner']


def memory() -> AgentMemory:
    url, store = os.environ.get('AGENT_MEMORY_URL', ''), read_setting('AGENT_MEMORY_STORE_ID')
    if not url or not store:
        raise LookupError('Agent Memory is not configured for this workspace.')
    return AgentMemory(url, store_id=store, api_key=os.environ.get('AGENT_MEMORY_API_KEY') or 'none',
                       timeout_ms=15000)


def text_of(event: dict[str, Any]) -> str:
    return ' '.join(part.get('text', '') for part in event.get('content') or [])


def settings() -> dict[str, Any]:
    control_plane = os.environ.get('AGENT_MEMORY_CONTROL_PLANE_URL', '')
    if not control_plane:
        return {'available': False, 'message': 'Store settings come from the Agent Memory Control Plane, '
                                               'which is available when Agent Memory is self-hosted.'}
    store = read_setting('AGENT_MEMORY_STORE_ID')
    request = Request(f'{control_plane}/v1/stores/{store}', headers={
        'Authorization': f'Bearer {read_setting("AGENT_MEMORY_ADMIN_TOKEN")}', 'Accept': 'application/json'})
    with urlopen(request, timeout=10) as response:
        stored = json.load(response)
    return {'available': True, 'storeId': store, 'settings': {key: stored[key] for key in SETTINGS if key in stored}}


def sessions() -> dict[str, Any]:
    return {'owner': owner(), 'sessions': memory().list_sessions(filter_owner_id=owner()).items}


def session(session_id: str) -> dict[str, Any]:
    stored = memory().get_session_memory(session_id=session_id).model_dump(mode='json', by_alias=True)
    if stored.get('ownerId') != owner():
        raise PermissionError('That session belongs to someone else.')
    return {'sessionId': session_id, 'events': [
        {'role': event['role'], 'actor': event.get('actorId'), 'createdAt': event.get('createdAt'), 'text': text_of(event)}
        for event in stored['events']
    ]}


def memories() -> dict[str, Any]:
    items = memory().search_long_term_memory(request={
        'filter_': {'owner_id': {'eq': owner()}}, 'limit': 50,
    }).model_dump(mode='json', by_alias=True)['items']
    return {'owner': owner(), 'memories': [
        {'text': item['text'], 'type': item.get('memoryType'), 'createdAt': item.get('createdAt')} for item in items
    ]}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split('?', 1)[0]
        routes = {'/memory/api/settings': settings, '/memory/api/sessions': sessions, '/memory/api/memories': memories}
        if path in ('/memory/', '/memory/index.html'):
            return self.send(200, PAGE, 'text/html; charset=utf-8')
        try:
            if path in routes:
                body = routes[path]()
            elif path.startswith('/memory/api/sessions/'):
                body = session(path.removeprefix('/memory/api/sessions/'))
            else:
                return self.send(404, b'Not found', 'text/plain')
            self.send(200, json.dumps(body).encode(), 'application/json')
        except (LookupError, PermissionError) as error:
            self.send(409, json.dumps({'error': str(error)}).encode(), 'application/json')
        except Exception as error:  # Service errors are shown in the page, never as a stack trace.
            status = getattr(error, 'status_code', None) or getattr(error, 'code', None)
            message = f'{type(error).__name__}' + (f' (HTTP {status})' if status else '') + ' from Agent Memory.'
            self.send(502, json.dumps({'error': message}).encode(), 'application/json')

    def send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        pass


if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', int(os.environ.get('INSPECTOR_PORT', '8093'))), Handler).serve_forever()
