"""Publish a supplied skill ZIP and retrieve its exact published version via SDK.

The instructor publishes once; attendees retrieve that entry by PLAYBOOK_SKILL_ID
and only need read access.
"""
from __future__ import annotations

import base64
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

from pydantic import BaseModel
from redis_agent_playbook import Playbook

from context import PublishedSkill


class Receipt(BaseModel):
    playbook_id: str
    owner: str
    entry_id: str
    version: int
    package_digest: str


def encode_package(folder: Path) -> str:
    """Create a deterministic Agent Skills ZIP rooted at the supplied folder name."""
    if not (folder / 'SKILL.md').is_file():
        raise ValueError('Skill folder must contain SKILL.md')
    buffer = BytesIO()
    with ZipFile(buffer, 'w', compression=ZIP_DEFLATED) as archive:
        for path in sorted(folder.rglob('*')):
            if path.is_symlink():
                raise ValueError('Skill packages must not contain symlinks')
            if path.is_file():
                name = folder.name + '/' + path.relative_to(folder).as_posix()
                archive.writestr(ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0)), path.read_bytes())
    return base64.b64encode(buffer.getvalue()).decode('ascii')


class PlaybookStore:
    def __init__(self, client: Playbook, playbook_id: str, receipt_path: Path, owner: str,
                 skill_id: str | None = None) -> None:
        self.client = client
        self.playbook_id = playbook_id
        self.receipt_path = receipt_path
        self.owner = owner
        # Set for attendees: the instructor's published entry, shared by the whole room.
        self.skill_id = skill_id

    def save(self, receipt: Receipt) -> None:
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.receipt_path.with_suffix('.tmp')
        temporary.write_text(receipt.model_dump_json(indent=2), encoding='utf-8')
        temporary.replace(self.receipt_path)

    def receipt(self) -> Receipt:
        if not self.receipt_path.exists():
            raise ValueError('Publish the supplied skill first with /publish-skill.')
        result = Receipt.model_validate_json(self.receipt_path.read_text())
        if result.playbook_id != self.playbook_id or result.owner != self.owner:
            raise ValueError('Publication receipt belongs to a different service or learner.')
        return result

    def publish(self, folder: Path) -> Receipt:
        if self.skill_id and not self.receipt_path.exists():
            raise ValueError('Publishing is an instructor step. This workspace retrieves the '
                             f'instructor-published skill {self.skill_id}; run /skills to inspect it.')
        package = encode_package(folder)
        digest = sha256(base64.b64decode(package)).hexdigest()
        if self.receipt_path.exists():
            receipt = self.receipt()
            if self.skill_id and receipt.entry_id != self.skill_id:
                raise ValueError('PLAYBOOK_SKILL_ID does not match this publication receipt.')
            if receipt.package_digest != digest:
                # Changed content becomes the next version of the same entry, so consumers keep one ID.
                appended = self.client.append_skill_version(skill_id=receipt.entry_id, package_base64=package)
                receipt = receipt.model_copy(update={'version': appended.version.version, 'package_digest': digest})
                self.save(receipt)
        else:
            # A unique learner/content key prevents overwriting other users' publications.
            key = 'workshop-report-' + sha256((self.owner + digest).encode()).hexdigest()[:24]
            created = self.client.create_skill(package_base64=package, entry_key=key)
            receipt = Receipt(
                playbook_id=self.playbook_id, owner=self.owner,
                entry_id=created.entry.entry_id, version=created.version.version,
                package_digest=digest,
            )
            # Save the draft ID before publication so retry can recover without creating another entry.
            self.save(receipt)
        entry = self.client.get_skill(skill_id=receipt.entry_id)
        if entry.publication is None or entry.publication.version != receipt.version:
            entry = self.client.publish_skill(skill_id=receipt.entry_id, version=receipt.version)
        if entry.publication is None or entry.publication.version != receipt.version:
            raise ValueError('Service did not confirm the requested published version.')
        return receipt

    def entry_id(self) -> str:
        if self.skill_id:
            return self.skill_id
        if not self.receipt_path.exists():
            raise ValueError('No team skill selected. Set PLAYBOOK_SKILL_ID to the instructor-published '
                             'skill, or publish it first with /publish-skill.')
        return self.receipt().entry_id

    def retrieve(self, query: str) -> PublishedSkill | None:
        entry_id = self.entry_id()
        results = self.client.search_skills(query=query, limit=20)
        match = next((item for item in results.matches if item.entry_id == entry_id), None)
        if match is None:
            return None
        entry = self.client.get_skill(skill_id=match.entry_id)
        if entry.publication is None or entry.publication.version != match.version:
            raise ValueError('Publication changed during retrieval; repeat the request.')
        version = self.client.get_skill_version(skill_id=match.entry_id, version=match.version)
        skill = version.content.payload.skill
        return PublishedSkill(
            source=f'playbook://{self.playbook_id}/skills/{version.entry_id}/versions/{version.version}',
            version=version.version, instructions=skill.instructions, digest=version.content_digest,
        )
