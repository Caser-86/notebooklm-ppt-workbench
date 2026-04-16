from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    preferred_language: str = "zh-CN"


class JobCreate(BaseModel):
    job_type: str
    mode: str = "auto"
