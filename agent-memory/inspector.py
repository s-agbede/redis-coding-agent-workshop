"""Agent Memory inspector: this workspace's sessions, long-term memories and store settings.

Serves one page at /memory/ and a few JSON routes under /memory/api/. Sessions and memories
come from the Agent Memory data plane, scoped to the workspace's owner. Store settings come
from the Control Plane, which is only available when Agent Memory is self-hosted. Editing them
is for the instructor: every attendee shares the store, so it is off unless INSPECTOR_ALLOW_EDITS=1.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from redis_agent_memory import AgentMemory

WORKSPACE = Path(os.environ.get('WORKSPACE_ROOT', '/workspace'))
PAGE = Path(__file__).with_name('inspector.html').read_bytes()
# Only these store settings are shown; connection details and credentials never leave the server.
SETTINGS = ('name', 'shortMemory', 'longTermMemory', 'extractionStrategy', 'extractionCadence',
            'summarization', 'customMemoryTypes', 'longTermMemoryExclusions')
# Plain settings change with a PATCH of that setting. Custom memory types do not: the 0.7 update API
# silently ignores customMemoryTypes, so they have their own operations (add_custom_type, update_prompt).
EDITABLE = ('shortMemory', 'longTermMemory', 'extractionCadence', 'summarization', 'longTermMemoryExclusions')


class ControlPlaneRejected(ValueError):
    """The Control Plane refused a change; its message explains why."""


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


def control_plane(method: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    store = read_setting('AGENT_MEMORY_STORE_ID')
    request = Request(f'{os.environ["AGENT_MEMORY_CONTROL_PLANE_URL"]}/v1/stores/{store}', method=method,
                      data=json.dumps(body).encode() if body is not None else None, headers={
                          'Authorization': f'Bearer {read_setting("AGENT_MEMORY_ADMIN_TOKEN")}',
                          'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        with urlopen(request, timeout=15) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code in (400, 409, 422):
            detail = json.loads(error.read() or b'{}')
            raise ControlPlaneRejected(detail.get('detail') or detail.get('title') or f'HTTP {error.code}') from None
        raise


def shown(stored: dict[str, Any]) -> dict[str, Any]:
    return {'available': True, 'storeId': stored.get('storeId'), 'editable': os.environ.get('INSPECTOR_ALLOW_EDITS') == '1',
            'settings': {key: stored[key] for key in SETTINGS if key in stored}}


def settings() -> dict[str, Any]:
    if not os.environ.get('AGENT_MEMORY_CONTROL_PLANE_URL'):
        return {'available': False, 'message': 'Store settings come from the Agent Memory Control Plane, '
                                               'which is available when Agent Memory is self-hosted.'}
    return shown(control_plane('GET'))


def change(operation: dict[str, Any], applied: Any) -> dict[str, Any]:
    """Send one change, then confirm from a fresh read that the store really holds it."""
    if os.environ.get('INSPECTOR_ALLOW_EDITS') != '1':
        raise PermissionError('Editing store settings is switched off for this workspace (INSPECTOR_ALLOW_EDITS).')
    control_plane('PATCH', operation)
    stored = control_plane('GET')
    if not applied(stored):
        raise ControlPlaneRejected('The Control Plane accepted the change but the store does not show it.')
    return shown(stored)


def update_setting(name: str, value: Any) -> dict[str, Any]:
    if name not in EDITABLE:
        raise ControlPlaneRejected(f'{name} cannot be edited here.')
    return change({name: value}, lambda stored: name in stored)


def add_custom_type(memory_type: dict[str, Any]) -> dict[str, Any]:
    return change({'addCustomMemoryTypes': [memory_type]}, lambda stored: any(
        item.get('name') == memory_type.get('name') for item in stored.get('customMemoryTypes') or []))


def update_prompt(type_name: str, prompt: str) -> dict[str, Any]:
    return change({'updateCustomMemoryTypeStrategies': [{'typeName': type_name, 'prompt': prompt}]}, lambda stored: any(
        item.get('name') == type_name and (item.get('extractionStrategy') or {}).get('prompt') == prompt
        for item in stored.get('customMemoryTypes') or []))


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
        {'id': item.get('id'), 'text': item['text'], 'type': item.get('memoryType'), 'createdAt': item.get('createdAt')}
        for item in items
    ]}


def forget(memory_id: str) -> dict[str, Any]:
    """Delete one of this workspace owner's long-term memories. Your own data, so no instructor switch."""
    stored = memory().get_long_term_memory(memory_id=memory_id).model_dump(mode='json', by_alias=True)
    if stored.get('ownerId') != owner():
        raise PermissionError('That memory belongs to someone else.')
    memory().bulk_delete_long_term_memories(memory_ids=[memory_id])
    return {'forgotten': memory_id}


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

    def do_POST(self) -> None:
        path = self.path.split('?', 1)[0]
        # A JSON body cannot be sent cross-site without a CORS preflight, which this server never grants.
        if not path.startswith('/memory/api/') or self.headers.get('Content-Type') != 'application/json':
            return self.send(404, b'Not found', 'text/plain')
        try:
            body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
            if path.startswith('/memory/api/memories/') and path.endswith('/forget'):
                result = forget(path.removeprefix('/memory/api/memories/').removesuffix('/forget'))
            elif path == '/memory/api/custom-types':
                result = add_custom_type(body.get('value'))
            elif path.startswith('/memory/api/custom-types/') and path.endswith('/prompt'):
                result = update_prompt(path.removeprefix('/memory/api/custom-types/').removesuffix('/prompt'), body.get('prompt', ''))
            elif path.startswith('/memory/api/settings/'):
                result = update_setting(path.removeprefix('/memory/api/settings/'), body.get('value'))
            else:
                return self.send(404, b'Not found', 'text/plain')
            self.send(200, json.dumps(result).encode(), 'application/json')
        except (ControlPlaneRejected, json.JSONDecodeError) as error:
            self.send(400, json.dumps({'error': str(error)}).encode(), 'application/json')
        except PermissionError as error:
            self.send(403, json.dumps({'error': str(error)}).encode(), 'application/json')
        except Exception as error:
            self.send(502, json.dumps({'error': f'{type(error).__name__} from the Control Plane.'}).encode(), 'application/json')

    def do_HEAD(self) -> None:
        # The workbench checks a panel is ready with HEAD before showing it.
        found = self.path.split('?', 1)[0] in ('/memory/', '/memory/index.html')
        self.send_response(200 if found else 404)
        self.send_header('Content-Type', 'text/html; charset=utf-8' if found else 'text/plain')
        self.end_headers()

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
