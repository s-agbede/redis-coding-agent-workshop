"""Start from repo root: uv run --group iris python main.py."""
from __future__ import annotations

import argparse
from contextlib import ExitStack
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
import completion
from runtime import COMMANDS, Workshop


def memory_store_id() -> str:
    """The store ID from AGENT_MEMORY_STORE_ID, or from the file a self-hosted setup writes."""
    path = os.environ.get('AGENT_MEMORY_STORE_ID_FILE', '')
    if not os.environ.get('AGENT_MEMORY_STORE_ID') and path and Path(path).is_file():
        return Path(path).read_text().strip()
    return os.environ.get('AGENT_MEMORY_STORE_ID', '')


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
    required = ('CAPTURE', 'RECALL', 'PLAYBOOK', 'handle')
    if not all(hasattr(learner, name) for name in required):
        parser.error('This agent.py is from an older workshop. Back it up and copy the starter agent.py.')
    with ExitStack() as stack:
        client = stack.enter_context(OpenAI(
            api_key=os.environ['AGENT_API_KEY'], base_url=os.environ.get('AGENT_BASE_URL') or None,
            timeout=float(os.environ.get('AGENT_REQUEST_TIMEOUT','90')), max_retries=0,
        ))
        memory = None
        store_id = memory_store_id()
        if os.environ.get('AGENT_MEMORY_URL') and store_id:
            # A self-hosted store has no API key; the hosted service requires one.
            memory = stack.enter_context(AgentMemory(
                os.environ['AGENT_MEMORY_URL'], store_id=store_id,
                api_key=os.environ.get('AGENT_MEMORY_API_KEY') or 'none', timeout_ms=30000,
            ))
        playbook = None
        playbook_keys = ('PLAYBOOK_DATA_PLANE_URL','PLAYBOOK_PLAYBOOK_ID','PLAYBOOK_API_KEY')
        if all(os.environ.get(key) for key in playbook_keys):
            sdk = stack.enter_context(Playbook(
                os.environ['PLAYBOOK_DATA_PLANE_URL'], playbook_id=os.environ['PLAYBOOK_PLAYBOOK_ID'],
                api_key=os.environ['PLAYBOOK_API_KEY'], timeout_ms=30000,
            ))
            playbook = PlaybookStore(sdk, args.output / 'publication.json',
                                     skill_id=os.environ.get('PLAYBOOK_SKILL_ID') or None)
        app = Workshop(learner, client, memory, playbook, owner, args.project, args.output)
        print('Coding agent with memory. /help lists commands.')
        app.command('/status')
        commands = completion.connect(COMMANDS)
        read = completion.prompt_reader(commands)
        while True:
            try:
                prompt = read('You > ').strip()
            except (EOFError, KeyboardInterrupt):
                break
            if prompt.lower() in ('exit','quit'):
                break
            if not prompt:
                continue
            try:
                if prompt.startswith('/'):
                    app.command(prompt)
                    commands.used(prompt.split()[0])
                else:
                    app.turn(prompt)
            except (ValueError, NotImplementedError, FileNotFoundError) as error:
                print(f'Error: {error or type(error).__name__}')
            except Exception as error:
                # Service exceptions can include request details; keep credentials out of the terminal.
                status = getattr(error, 'status_code', None)
                print(f'Error: {type(error).__name__}' + (f' (HTTP {status})' if status else '') + '. Check the settings in .env.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
