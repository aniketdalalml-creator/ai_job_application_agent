from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ProfileIn(BaseModel):
    resume_text: str = ""
    target_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    years_experience: float = 0.0
    locations: list[str] = Field(default_factory=list)
    work_mode: Literal["on-site", "remote", "hybrid"] = "hybrid"
    country: str = "us"


class ProfileOut(ProfileIn):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    updated_at: datetime
