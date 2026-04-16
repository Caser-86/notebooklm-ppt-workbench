from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    preferred_language: str = "zh-CN"
    preferred_style: str = "default"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    job_type: str
    mode: str = "auto"
    status: str = "draft"
    attention_reason: str = ""
    notebook_session_path: str = ""
    retry_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
