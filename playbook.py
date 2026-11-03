"""Publish the team skill to Redis Agent Playbook, and retrieve it and approved answers for a task.

The instructor publishes once. Attendees set PLAYBOOK_SKILL_ID to that entry and only read.
"""
from __future__ import annotations

import base64
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from redis_agent_playbook import Playbook

from context import PublishedSkill, TeamAnswer


def encode_package(folder: Path) -> str:
    """Zip a skill folder as an Agent Skills package, byte-identical for identical content."""
    buffer = BytesIO()
    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
        for path in sorted(p for p in folder.rglob('*') if p.is_file() and not p.is_symlink()):
            name = folder.name + '/' + path.relative_to(folder).as_posix()
            archive.writestr(ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), path.read_bytes())
    return base64.b64encode(buffer.getvalue()).decode('ascii')


class PlaybookStore:
    def __init__(self, client: Playbook, receipt_path: Path, skill_id: str | None = None) -> None:
        self.client = client
        self.receipt_path = receipt_path
        self.skill_id = skill_id

    def publish(self, folder: Path) -> tuple[str, int]:
        """Publish the folder; changed content becomes the next version of the same entry."""
        receipt = json.loads(self.receipt_path.read_text()) if self.receipt_path.exists() else None
        if self.skill_id and receipt is None:
            raise ValueError('Publishing is done by the instructor. Run /skills to see the team procedure.')
        package = encode_package(folder)
        digest = sha256(package.encode()).hexdigest()
        if receipt and receipt['digest'] == digest:
            return receipt['entry_id'], receipt['version']
        if receipt:
            created = self.client.append_skill_version(skill_id=receipt['entry_id'], package_base64=package)
        else:
            created = self.client.create_skill(package_base64=package, entry_key=f'report-validation-{digest[:12]}')
        entry_id, version = created.entry.entry_id, created.version.version
        self.client.publish_skill(skill_id=entry_id, version=version)
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        self.receipt_path.write_text(json.dumps({'entry_id': entry_id, 'version': version, 'digest': digest}))
        return entry_id, version

    def entry_id(self) -> str:
        if self.skill_id:
            return self.skill_id
        if not self.receipt_path.exists():
            raise ValueError('No team skill yet. Set PLAYBOOK_SKILL_ID, or publish it with /publish-skill.')
        return json.loads(self.receipt_path.read_text())['entry_id']

    def retrieve(self, query: str, min_score: float = 0.0) -> PublishedSkill | None:
        """Search the Playbook for this task; return the team skill if it scores at least min_score."""
        entry_id = self.entry_id()
        matches = self.client.search_skills(query=query, limit=20).matches
        match = next((item for item in matches if item.entry_id == entry_id and (item.score or 0) >= min_score), None)
        if match is None:
            return None
        content = self.client.get_skill_version(skill_id=entry_id, version=match.version).content.payload.skill
        return PublishedSkill(name=content.manifest.name, version=match.version, instructions=content.instructions)

    def answers(self, query: str, min_score: float = 0.0) -> list[TeamAnswer]:
        """Published FAQs that fit this task. Proposals only become FAQs once a person accepts and publishes them."""
        matches = self.client.search_faqs(query=query, limit=3).matches
        return [TeamAnswer(question=item.faq.question, answer=item.faq.answer, version=item.version)
                for item in matches if (item.score or 0) >= min_score]
