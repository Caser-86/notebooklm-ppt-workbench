from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    preferred_language: str = "zh-CN"


class ProjectDetailRead(BaseModel):
    id: int
    title: str
    preferred_language: str
    preferred_style: str
    brief: str
    prompt_draft: str
    source_manifest: dict


class ProjectUpdate(BaseModel):
    brief: str = ""
    prompt_draft: str = ""
    source_manifest: dict = {}


class JobCreate(BaseModel):
    job_type: str
    mode: str = "auto"


class ArtifactLink(BaseModel):
    id: str
    label: str
    href: str


class RebuildVersionRead(BaseModel):
    id: int
    version_number: int
    slide_count: int
    artifacts: list[ArtifactLink]
