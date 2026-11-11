"""Create the workshop's own Redis Agent Playbook in a local Iris on-prem preview.

    uv run --group iris python scripts/iris_preview_playbook.py

Creates the "BofA Coding Agent Workshop" Playbook once, issues a read-only key for attendees
through the identity service, and publishes the team knowledge from this repository:
every skill folder in skills/ and every FAQ in faqs/faqs.json. A skill whose text changed gets a
new published version; everything else is left as it is, so it is safe to run again. The key and Playbook ID are saved to the preview's private
.demo/local/workshop-playbook.json; scripts/use_iris_preview.sh picks them up.

The report-validation skill is published through PlaybookStore, so /publish-skill keeps adding
versions to the same entry afterwards.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from redis_agent_playbook import Playbook

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from playbook import PlaybookStore, encode_package  # noqa: E402

PREVIEW = Path(os.environ.get('IRIS_PREVIEW_DIR', Path.home() / 'Documents/Projects/iris-onprem-preview'))
SAVED = PREVIEW / '.demo/local/workshop-playbook.json'
RECEIPT = ROOT / 'output/iris-preview/publication.json'
CONTROL_PLANE, IDENTITY, DATA_PLANE = 'http://127.0.0.1:19201', 'http://127.0.0.1:19200', 'http://127.0.0.1:19202'
NAME = 'BofA Coding Agent Workshop'
PLAYBOOK = {
    'name': NAME,
    'embedding': {'provider': 'openai', 'model': 'text-embedding-3-small', 'dimensions': 1536},
    # The agent applies its own, stricter thresholds (SKILL_MIN_SCORE, FAQ_MIN_SCORE).
    'discovery': {'faqMinimumScore': 0.3, 'skillMinimumScore': 0.3, 'maxResults': 10},
    'proposalPolicy': {'reviewWindowSeconds': 1209600, 'maxOpenProposals': 5000},
}
TEAM_SKILL = 'report-validation'  # versioned by /publish-skill


def call(base: str, method: str, path: str, token: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    request = Request(base + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                      headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def playbook_id(token: str) -> str:
    existing = [p for p in call(CONTROL_PLANE, 'GET', '/v1/playbooks', token)['playbooks'] if p['name'] == NAME]
    created = existing[0] if existing else call(CONTROL_PLANE, 'POST', '/v1/playbooks', token, PLAYBOOK)
    for _ in range(30):
        if created['state'] == 'ready':
            return created['playbookId']
        time.sleep(2)
        created = call(CONTROL_PLANE, 'GET', f'/v1/playbooks/{created["playbookId"]}', token)
    raise SystemExit(f'Playbook {created["playbookId"]} is still {created["state"]}; run this again shortly.')


def attendee_key(token: str, playbook: str) -> None:
    saved = json.loads(SAVED.read_text()) if SAVED.exists() else {}
    if saved.get('playbook_id') == playbook:
        return
    key = call(IDENTITY, 'POST', '/v1/api-keys', token, {
        'name': f'coding-agent-workshop-{playbook[3:11]}',
        'grants': [{'product': 'playbook', 'tenant': '1', 'resourceType': 'playbook',
                    'resourceId': playbook, 'actions': ['read']}],
    })
    SAVED.write_text(json.dumps({'playbook_id': playbook, 'api_key': key['token'], 'key_id': key['keyId']}))
    SAVED.chmod(0o600)


def skill_text(folder: Path) -> tuple[str, str]:
    """A SKILL.md's description and instructions, as Playbook stores them."""
    _, frontmatter, body = (folder / 'SKILL.md').read_text().split('---', 2)
    description = next(line.split(':', 1)[1].strip() for line in frontmatter.splitlines() if line.startswith('description:'))
    return description, body.strip()


def publish_skills(sdk: Playbook) -> None:
    existing = {item.entry_key: item for item in sdk.list_skills(limit=100).skills}
    for folder in sorted(p for p in (ROOT / 'skills').iterdir() if (p / 'SKILL.md').is_file()):
        if folder.name == TEAM_SKILL:
            entry, version = PlaybookStore(sdk, RECEIPT).publish(folder)
            print(f'Skill {folder.name}: version {version}')
            continue
        entry = existing.get(folder.name)
        if entry is None:
            created = sdk.create_skill(package_base64=encode_package(folder), entry_key=folder.name)
        else:
            published = sdk.get_skill_version(skill_id=entry.entry_id, version=entry.publication.version).content.payload.skill
            if (published.manifest.description, published.instructions.strip()) == skill_text(folder):
                print(f'Skill {folder.name}: version {entry.publication.version}, unchanged')
                continue
            created = sdk.append_skill_version(skill_id=entry.entry_id, package_base64=encode_package(folder))
        sdk.publish_skill(skill_id=created.entry.entry_id, version=created.version.version)
        print(f'Skill {folder.name}: version {created.version.version} published')


def publish_faqs(sdk: Playbook) -> None:
    existing = {item.entry_key for item in sdk.list_faqs(limit=100).faqs}
    for faq in json.loads((ROOT / 'faqs/faqs.json').read_text()):
        if faq['key'] in existing:
            print(f'FAQ {faq["key"]}: already there')
            continue
        created = sdk.create_faq(entry_key=faq['key'], content={
            'payload': {'faq': {'question': faq['question'], 'answer': faq['answer']}}, 'intents': faq['intents']})
        sdk.publish_faq(faq_id=created.entry.entry_id, version=created.version.version)
        print(f'FAQ {faq["key"]}: published')


def main() -> None:
    subprocess.run(['task', 'token', 'PRODUCT=playbook'], cwd=PREVIEW, check=True, capture_output=True)
    token = (PREVIEW / '.demo/local/operator.jwt').read_text().strip()
    playbook = playbook_id(token)
    attendee_key(token, playbook)
    receipt = json.loads(RECEIPT.read_text()) if RECEIPT.exists() else {}
    if receipt and receipt.get('playbook_id') != playbook:
        # The receipt records another Playbook's entry; keep it, and start fresh for this one.
        RECEIPT.rename(RECEIPT.with_name(f'publication-{receipt.get("playbook_id", "previous")}.json'))
    with Playbook(DATA_PLANE, playbook_id=playbook, api_key=token) as sdk:
        publish_skills(sdk)
        publish_faqs(sdk)
    saved = json.loads(RECEIPT.read_text())
    RECEIPT.write_text(json.dumps({**saved, 'playbook_id': playbook}))
    print(f'Playbook "{NAME}": {playbook} (attendee key saved privately in {SAVED})')


if __name__ == '__main__':
    main()
