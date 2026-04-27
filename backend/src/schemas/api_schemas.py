from datetime import datetime

from pydantic import BaseModel, field_validator


class AnalyzePipelineInput(BaseModel):
    """Validated payload passed to the agent pipeline after merging file + text."""

    title: str
    raw_case_text: str

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        t = v.strip()
        if not t:
            raise ValueError("title must not be blank")
        return t

    @field_validator("raw_case_text")
    @classmethod
    def case_not_blank(cls, v: str) -> str:
        t = (v or "").strip()
        if not t:
            raise ValueError("merged case text must not be blank")
        return t


class AgentStepOut(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    step_name: str
    step_index: int
    status: str
    result: dict | None


class HistoryItem(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    raw_input: str
    status: str
    created_at: datetime


class HistoryDetail(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: str
    raw_input: str
    status: str
    created_at: datetime
    steps: list[AgentStepOut]


class CurrentUser(BaseModel):
    user_id: str
    email: str | None = None
