from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, Integer, JSON, Text, UniqueConstraint
from sqlmodel import Field, SQLModel

from backend.app.models.base import new_id, utcnow


class SearchRun(SQLModel, table=True):
    __tablename__ = "search_runs"

    id: str = Field(default_factory=new_id, primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    status: str = Field(default="queued", max_length=32, index=True)
    query: str = Field(default="", max_length=512)
    filters: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    result_count: int = Field(default=0, sa_column=Column(Integer, nullable=False))
    avg_fit: float = Field(default=0.0, sa_column=Column(Float, nullable=False))
    error: str = Field(default="", sa_column=Column(Text, nullable=False))
    events: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))
    finished_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime, nullable=True))


class Job(SQLModel, table=True):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("user_id", "source", "external_id", name="uq_job_source"),)

    id: str = Field(default_factory=new_id, primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    search_run_id: Optional[str] = Field(default=None, foreign_key="search_runs.id", max_length=36)
    source: str = Field(default="adzuna", max_length=64)
    external_id: str = Field(max_length=255, index=True)
    title: str = Field(default="", max_length=512)
    company: str = Field(default="", max_length=255)
    location: str = Field(default="", max_length=255)
    description: str = Field(default="", sa_column=Column(Text, nullable=False))
    url: str = Field(default="", sa_column=Column(Text, nullable=False))
    raw: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
