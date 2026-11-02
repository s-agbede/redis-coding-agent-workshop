"""Typed boundary for a procedure retrieved from an exact Playbook version."""
from pydantic import BaseModel, ConfigDict


class PublishedSkill(BaseModel):
    model_config = ConfigDict(frozen=True)
    source: str
    version: int
    instructions: str
    digest: str
