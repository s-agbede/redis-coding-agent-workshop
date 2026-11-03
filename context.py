"""A team procedure retrieved from Redis Agent Playbook."""
from pydantic import BaseModel, ConfigDict


class PublishedSkill(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    version: int
    instructions: str
