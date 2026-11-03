"""Team knowledge retrieved from Redis Agent Playbook: a procedure (skill) or an approved answer (FAQ)."""
from pydantic import BaseModel, ConfigDict


class PublishedSkill(BaseModel):
    model_config = ConfigDict(frozen=True)
    name: str
    version: int
    instructions: str


class TeamAnswer(BaseModel):
    model_config = ConfigDict(frozen=True)
    question: str
    answer: str
    version: int
