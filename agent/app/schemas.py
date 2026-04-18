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
    insight_summary: str


class ProjectUpdate(BaseModel):
    brief: str = ""
    prompt_draft: str = ""
    source_manifest: dict = {}


class SourceRevisionRead(BaseModel):
    id: int
    revision_number: int
    source_manifest: dict
    insight_summary: str


class ImportedSlideAssetRead(BaseModel):
    id: int
    slide_index: int
    preview_image_path: str
    text_dump: str
    structure_json_path: str


class ImportedPresentationRead(BaseModel):
    id: int
    project_id: int
    source_type: str
    filename: str
    status: str
    page_count: int
    error_message: str
    object_summary: dict[str, int] = {}
    slide_assets: list[ImportedSlideAssetRead] = []


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
