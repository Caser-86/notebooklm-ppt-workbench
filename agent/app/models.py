from datetime import UTC, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    preferred_language: str = "zh-CN"
    preferred_style: str = "default"
    brief: str = ""
    prompt_draft: str = ""
    source_manifest_json: str = "{}"
    insight_summary: str = ""
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


class RebuildVersion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    version_number: int
    slide_count: int = 0
    display_clone_path: str
    editable_rebuild_path: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SourceRevision(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(index=True)
    revision_number: int
    source_manifest_json: str
    insight_summary: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
