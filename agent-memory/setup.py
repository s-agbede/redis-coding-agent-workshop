"""Prepare a self-hosted Redis Agent Memory 0.7 for the workshop.

    python setup.py config     write the data plane and Control Plane configuration, and an admin token
    python setup.py provision  create the workshop store (once) and save its ID for the runtime

The configuration follows the published Agent Memory 0.7.0 release, as used in
redis-developer/raphael-workshops (python/6_agent_memory).
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import sys
import time
from urllib.error import URLError
from urllib.request import Request, urlopen

CONFIG = Path('/run/ram')
TOKEN = Path('/run/ram-token/admin-token')
STATE = Path('/run/agent-memory')
STORE_REQUEST = Path(__file__).with_name('store.json')
REDIS = 'redis://memory-redis:6379/0'
CONTROL_PLANE = 'http://memory-control-plane:9100'


def configs(api_key: str, model: str) -> tuple[dict, dict]:
    metadata = {'urls': [REDIS], 'namespace': 'workshop:ram:metadata'}
    databases = {'1': {'name': 'workshop', 'urls': [REDIS]}}
    llm = {'provider': 'openai', 'credentials': {'type': 'static', 'api_key': api_key},
           'models': {'default_chat_model': model}}
    data_plane = {
        'server': {'host': '0.0.0.0', 'port': 9000},
        'license': {'license_path': '/run/license'},
        'default_extraction_strategy': 'instruct',
        'request_region': {'default': 'workshop'},
        'background_jobs': {
            'redis': {'enabled': True, 'queue_prefix': 'workshop', 'urls': [REDIS],
                      'worker_regions': ['workshop'], 'defaults': {'concurrency': 1}},
            'idempotency': {'enabled': True, 'urls': [REDIS], 'done_ttl': '24h', 'lock_ttl': '5m',
                            'lease_extension_interval': '1m', 'operation_timeout': '5s'},
        },
        'metadata': metadata,
        'databases': databases,
        'embedding': {'provider': 'openai', 'models': {
            'default_embedding_model': 'text-embedding-3-large', 'dimensions': 3072}},
        'auth': {'method': 'none'},
        'embedders_connection_details': {'openai': {
            'base_url': 'https://api.openai.com', 'credentials': {'type': 'static', 'api_key': api_key}}},
        'inference_providers': {'openai': {'endpoint': {
            'base_url': 'https://api.openai.com/v1', 'auth_format': 'bearer'}}},
        'dataplane_client': {'base_url': 'http://memory-server:9000', 'auth': {'disabled': True}},
        'session_summarisation': {'enabled': True, 'llm': llm},
        'custom_extraction': {'enabled': True},
        'promote_session_memory': {'strategies': {
            'instruct': {'promotion_deduplication_window': '0s', 'llm': llm},
            'custom_extraction': {'promotion_deduplication_window': '0s', 'llm': llm},
        }},
    }
    control_plane = {
        'server': {'host': '0.0.0.0', 'port': 9100},
        'profile': 'prod',
        'auth': {'type': 'admin-token', 'admin_token': {'token_file': str(TOKEN)}},
        'license': {'license_path': '/run/license'},
        'metadata': metadata,
        'databases': databases,
        'embedding': {'dimensions': 3072},
    }
    return data_plane, control_plane


def write_config() -> None:
    if not Path('/run/license').is_file():
        sys.exit('Set AGENT_MEMORY_LICENSE_FILE in .env to your Agent Memory license file.')
    api_key = os.environ.get('OPENAI_API_KEY', '').strip()
    if not api_key:
        sys.exit('Self-hosted Agent Memory needs an OpenAI key for extraction (AGENT_API_KEY in .env).')
    data_plane, control_plane = configs(api_key, os.environ.get('MEMORY_MODEL') or 'gpt-4o-mini')
    CONFIG.mkdir(parents=True, exist_ok=True)
    # JSON is valid YAML; the .yaml extension selects the services' YAML loader.
    for name, config in (('data-plane.yaml', data_plane), ('control-plane.yaml', control_plane)):
        (CONFIG / name).write_text(json.dumps(config, indent=2))
        (CONFIG / name).chmod(0o444)
    TOKEN.parent.mkdir(parents=True, exist_ok=True)
    if not TOKEN.exists():
        TOKEN.write_text(secrets.token_urlsafe(48))
    TOKEN.chmod(0o444)  # The services run as a non-root user.
    print('Agent Memory configuration written.')


def control_plane(method: str, path: str, body: dict | None = None) -> dict:
    request = Request(CONTROL_PLANE + path, method=method,
                      data=json.dumps(body).encode() if body is not None else None,
                      headers={'Authorization': f'Bearer {TOKEN.read_text().strip()}',
                               'Content-Type': 'application/json', 'Accept': 'application/json'})
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def provision() -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    request = json.loads(STORE_REQUEST.read_text())
    for _ in range(60):
        try:
            stores = control_plane('GET', '/v1/stores')['stores']
            break
        except (URLError, ConnectionError):
            time.sleep(2)
    else:
        sys.exit('The Agent Memory Control Plane did not become ready.')
    existing = [store for store in stores if store.get('name') == request['name']]
    store_id = existing[0]['storeId'] if existing else control_plane('POST', '/v1/stores', request)['storeId']
    (STATE / 'store-id').write_text(store_id)
    print(f'Agent Memory store {request["name"]} ready: {store_id}')


if __name__ == '__main__':
    {'config': write_config, 'provision': provision}[sys.argv[1]]()
