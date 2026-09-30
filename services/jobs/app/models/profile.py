from pydantic import BaseModel, Field


class ProfileRead(BaseModel):
    target_job_titles: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    timezone: str = "UTC"


class ProfileUpdate(BaseModel):
    target_job_titles: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    timezone: str = "UTC"
