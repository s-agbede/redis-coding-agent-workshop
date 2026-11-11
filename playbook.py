"""Publish the team skill to Redis Agent Playbook, and retrieve the team knowledge that fits a task.

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
        self.receipt_path.write_text(json.dumps({**(receipt or {}), 'entry_id': entry_id, 'version': version, 'digest': digest}))
        return entry_id, version

    def retrieve(self, query: str, min_score: float = 0.0) -> PublishedSkill | None:
        """The published team skill that best fits this task, if it scores at least min_score."""
        matches = self.client.search_skills(query=query, limit=5).matches
        best = max(matches, key=lambda item: item.score or 0, default=None)
        if best is None or (best.score or 0) < min_score:
            return None
        return self._skill(best.entry_id, best.version)

    def published_skills(self) -> list[PublishedSkill]:
        """Every skill an agent can be given right now: each entry's published version."""
        entries = self.client.list_skills(published=True, limit=50).skills
        return [self._skill(entry.entry_id, entry.publication.version) for entry in entries if entry.publication]

    def _skill(self, entry_id: str, version: int) -> PublishedSkill:
        content = self.client.get_skill_version(skill_id=entry_id, version=version).content.payload.skill
        return PublishedSkill(name=content.manifest.name, version=version, instructions=content.instructions)

    def answers(self, query: str, min_score: float = 0.0) -> list[TeamAnswer]:
        """Published FAQs that fit this task. Proposals only become FAQs once a person accepts and publishes them."""
        matches = self.client.search_faqs(query=query, limit=3).matches
        return [TeamAnswer(question=item.faq.question, answer=item.faq.answer, version=item.version)
                for item in matches if (item.score or 0) >= min_score]
