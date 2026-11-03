"""Create the workshop's own Agent Memory store in a local Iris on-prem preview.

    python3 scripts/iris_preview_store.py

Uses agent-memory/store.json (including the coding_preference custom memory type), creates the store
once through the Memory Control Plane, issues a read/write key for it through the identity service,
and saves both to the preview's private .demo/local/workshop-memory.json. Safe to run again.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PREVIEW = Path(os.environ.get('IRIS_PREVIEW_DIR', Path.home() / 'Documents/Projects/iris-onprem-preview'))
SAVED = PREVIEW / '.demo/local/workshop-memory.json'
CONTROL_PLANE, IDENTITY = 'http://127.0.0.1:19100', 'http://127.0.0.1:19200'


def call(base: str, method: str, path: str, token: str, body: dict | None = None) -> dict:
    request = Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                      headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                               'Accept': 'application/json'})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def main() -> None:
    subprocess.run(['task', 'token', 'PRODUCT=memory'], cwd=PREVIEW, check=True, capture_output=True)
    token = (PREVIEW / '.demo/local/operator.jwt').read_text().strip()
    request = json.loads((ROOT / 'agent-memory/store.json').read_text())
    saved = json.loads(SAVED.read_text()) if SAVED.exists() else {}
    stores = call(CONTROL_PLANE, 'GET', '/v1/stores', token)['stores']
    existing = [store for store in stores if store.get('name') == request['name']]
    store_id = existing[0]['storeId'] if existing else call(CONTROL_PLANE, 'POST', '/v1/stores', token, request)['storeId']
    if saved.get('store_id') != store_id:
        key = call(IDENTITY, 'POST', '/v1/api-keys', token, {
            'name': f'coding-agent-workshop-{store_id[:8]}',
            'grants': [{'product': 'memory', 'tenant': '1', 'resourceType': 'mem-store',
                        'resourceId': store_id, 'actions': ['read', 'write']}],
        })
        saved = {'store_id': store_id, 'api_key': key['token'], 'key_id': key['keyId']}
        SAVED.write_text(json.dumps(saved))
        SAVED.chmod(0o600)
    print(f'Workshop memory store {request["name"]}: {store_id} (key saved privately in {SAVED})')


if __name__ == '__main__':
    main()
