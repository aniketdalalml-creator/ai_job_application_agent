from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, JSON, Text
from sqlmodel import Field, SQLModel

from backend.app.models.base import new_id, utcnow


class Application(SQLModel, table=True):
    __tablename__ = "applications"

    id: str = Field(default_factory=new_id, primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    job_id: str = Field(foreign_key="jobs.id", index=True, max_length=36)
    status: str = Field(default="saved", max_length=32, index=True)
    cover_letter: str = Field(default="", sa_column=Column(Text, nullable=False))
    resume_bullets: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    research: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    critique: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    revised: bool = Field(default=False)
    notes: str = Field(default="", sa_column=Column(Text, nullable=False))
    error: str = Field(default="", sa_column=Column(Text, nullable=False))
    events: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
    applied_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
