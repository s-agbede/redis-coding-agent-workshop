"""Point the workshop Playbook's FAQ extraction at the workshop's Agent Memory store.

    uv run python scripts/iris_preview_extraction.py [--idle-seconds 60]

Playbook reads finished sessions from one Agent Memory store and drafts FAQ proposals
for a person to review in the Iris UI (Playbook > Proposals). A Playbook has one
extraction binding and its source store cannot be changed in place, so a binding for a
different store is deleted and recreated. Idempotent: a matching binding is left alone.
Uses the preview's operator token; prints no secrets.
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = Path.home() / 'Documents/Projects/iris-onprem-preview/.demo/local'
CONTROL_PLANE = 'http://127.0.0.1:19201'


def call(method: str, path: str, token: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(
        CONTROL_PLANE + path, method=method, data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
    )
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read() or b'{}')
    except urllib.error.HTTPError as error:
        raise SystemExit(f'{method} {path} failed: HTTP {error.code} {error.read().decode()[:300]}') from error


def wait_until_settled(bindings: str, binding_id: str, token: str) -> dict[str, Any]:
    for _ in range(30):
        binding = call('GET', f'{bindings}/{binding_id}', token)
        if binding['status'] in ('ready', 'blocked'):
            return binding
        time.sleep(2)
    raise SystemExit(f'Binding {binding_id} is still {binding["status"]}; try again shortly.')


def wait_until_gone(bindings: str, binding_id: str, token: str) -> None:
    """Deletion is asynchronous: wait until the binding no longer appears."""
    for _ in range(60):
        if all(binding['bindingId'] != binding_id for binding in call('GET', bindings, token)['bindings']):
            return
        time.sleep(2)
    raise SystemExit(f'Binding {binding_id} is still being deleted; run this again shortly.')


def pause_other_playbooks(token: str, store_id: str, keep: str) -> None:
    """Pause other Playbooks' bindings to this store, so proposals land only in the workshop's Playbook."""
    for playbook in call('GET', '/v1/playbooks', token)['playbooks']:
        if playbook['playbookId'] == keep:
            continue
        path = f'/v1/playbooks/{playbook["playbookId"]}/extraction/bindings'
        for binding in call('GET', path, token)['bindings']:
            if binding['source']['storeId'] == store_id and binding['enabled']:
                call('PATCH', f'{path}/{binding["bindingId"]}', token, {'expectedVersion': binding['version'], 'enabled': False})
                print(f'Paused extraction into "{playbook["name"]}".')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--idle-seconds', type=int, default=60,
                        help='How long a session must be idle before extraction reads it (60-86400).')
    args = parser.parse_args()
    token = (PREVIEW / 'operator.jwt').read_text().strip()
    workshop = PREVIEW / 'workshop-playbook.json'  # from scripts/iris_preview_playbook.py
    playbook_id = (json.loads(workshop.read_text())['playbook_id'] if workshop.exists()
                   else json.loads((PREVIEW / 'connections.json').read_text())['products']['playbook']['resource_id'])
    store_id = json.loads((PREVIEW / 'workshop-memory.json').read_text())['store_id']
    bindings = f'/v1/playbooks/{playbook_id}/extraction/bindings'
    pause_other_playbooks(token, store_id, playbook_id)
    job = {'type': 'faq', 'idleWindowSeconds': args.idle_seconds}

    for binding in call('GET', bindings, token)['bindings']:
        if binding['source']['storeId'] == store_id:
            if binding['job'] != job or not binding['enabled']:
                binding = call('PATCH', f'{bindings}/{binding["bindingId"]}', token,
                               {'expectedVersion': binding['version'], 'job': job, 'enabled': True})
            print(f'Extraction reads store {store_id[:8]}… (idle {args.idle_seconds}s, {binding["status"]}).')
            return
        call('DELETE', f'{bindings}/{binding["bindingId"]}', token)
        wait_until_gone(bindings, binding['bindingId'], token)
        print(f'Removed the binding for store {binding["source"]["storeId"][:8]}….')

    created = call('POST', bindings, token, {'source': {'type': 'redis_agent_memory', 'storeId': store_id}, 'job': job})
    binding = wait_until_settled(bindings, created['bindingId'], token)
    if binding['status'] != 'ready':
        raise SystemExit(f'Binding is {binding["status"]}: Playbook could not get access to the store.')
    call('PATCH', f'{bindings}/{binding["bindingId"]}', token, {'expectedVersion': binding['version'], 'enabled': True})
    print(f'Extraction now reads store {store_id[:8]}… (idle {args.idle_seconds}s). Proposals appear in the Iris UI.')


if __name__ == '__main__':
    main()
