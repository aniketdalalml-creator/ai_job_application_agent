from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime, JSON, Text
from sqlmodel import Field, SQLModel

from backend.app.models.base import new_id, utcnow


class Profile(SQLModel, table=True):
    __tablename__ = "profiles"

    id: str = Field(default_factory=new_id, primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", unique=True, index=True, max_length=36)
    resume_text: str = Field(default="", sa_column=Column(Text, nullable=False))
    target_titles: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    skills: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    years_experience: float = Field(default=0.0)
    locations: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    work_mode: str = Field(default="hybrid", max_length=32)
    country: str = Field(default="us", max_length=8)
    updated_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
