"""Start from repo root: uv run --group iris python main.py."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parent
# Direct script invocation works identically in the repository and browser workspace.
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from openai import OpenAI
from redis_agent_memory import AgentMemory
from redis_agent_playbook import Playbook

from playbook import PlaybookStore
from runtime import Workshop


def main() -> int:
    load_dotenv(ROOT / '.env')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=ROOT / 'project')
    parser.add_argument('--agent', type=Path, default=ROOT / 'agent.py', help='Explicit instructor reference or learner file')
    parser.add_argument('--owner', default=os.environ.get('IRIS_OWNER_ID'))
    parser.add_argument('--output', type=Path, default=ROOT / 'output/workshop')
    args = parser.parse_args()
    if not args.project.is_dir():
        parser.error('Project directory does not exist')
    if not os.environ.get('AGENT_API_KEY'):
        parser.error('Configure AGENT_API_KEY in the root .env')
    args.output.mkdir(parents=True, exist_ok=True)
    identity_file = args.output / 'owner.json'
    if args.owner:
        owner = args.owner
    elif identity_file.exists():
        owner = json.loads(identity_file.read_text())['owner']
    else:
        owner = 'learner-' + uuid4().hex
        identity_file.write_text(json.dumps({'owner': owner}))
    spec = importlib.util.spec_from_file_location('workshop_learner', args.agent.resolve())
    if spec is None or spec.loader is None:
        parser.error('Cannot load the selected learner agent')
    learner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(learner)
    required = ('CAPTURE_ENABLED', 'RECALL_ENABLED', 'PLAYBOOK_ENABLED')
    if not all(hasattr(learner, name) for name in required):
        parser.error('The selected agent belongs to an older workshop. Back it up and use the memory workshop starter agent.py from this branch.')
    with ExitStack() as stack:
        client = stack.enter_context(OpenAI(
            api_key=os.environ['AGENT_API_KEY'], base_url=os.environ.get('AGENT_BASE_URL') or None,
            timeout=float(os.environ.get('AGENT_REQUEST_TIMEOUT','90')), max_retries=0,
        ))
        memory = None
        memory_keys = ('AGENT_MEMORY_URL','AGENT_MEMORY_STORE_ID','AGENT_MEMORY_API_KEY')
        if all(os.environ.get(key) for key in memory_keys):
            memory = stack.enter_context(AgentMemory(
                os.environ['AGENT_MEMORY_URL'], store_id=os.environ['AGENT_MEMORY_STORE_ID'],
                api_key=os.environ['AGENT_MEMORY_API_KEY'], timeout_ms=30000,
            ))
        playbook = None
        playbook_keys = ('PLAYBOOK_DATA_PLANE_URL','PLAYBOOK_PLAYBOOK_ID','PLAYBOOK_API_KEY')
        if all(os.environ.get(key) for key in playbook_keys):
            sdk = stack.enter_context(Playbook(
                os.environ['PLAYBOOK_DATA_PLANE_URL'], playbook_id=os.environ['PLAYBOOK_PLAYBOOK_ID'],
                api_key=os.environ['PLAYBOOK_API_KEY'], timeout_ms=30000,
            ))
            receipt_file = args.output / ('publication-' + sha256(owner.encode()).hexdigest()[:16] + '.json')
            playbook = PlaybookStore(sdk, os.environ['PLAYBOOK_PLAYBOOK_ID'], receipt_file, owner,
                                     skill_id=os.environ.get('PLAYBOOK_SKILL_ID') or None)
        app = Workshop(learner, client, memory, playbook, owner, args.project, args.output)
        print('Memory workshop: one coding agent, persistent preferences and published skills. /help for commands.')
        print(f'Owner: {owner}\nSession: {app.state.session_id}\nProject: {args.project.resolve()}')
        app.command('/status')
        while True:
            try:
                prompt = input('You > ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if prompt.lower() in ('exit','quit'):
                break
            if not prompt:
                continue
            try:
                if prompt.startswith('/'):
                    app.command(prompt)
                else:
                    app.turn(prompt)
            except (ValueError, NotImplementedError, FileNotFoundError) as error:
                print(f'Action incomplete: {error}')
            except Exception as error:
                # Service exceptions can include request details; keep credentials out of terminal logs.
                print(f'Action incomplete: {type(error).__name__}; status={getattr(error,"status_code","unavailable")}. Check service connectivity/configuration. No successful result is implied.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
