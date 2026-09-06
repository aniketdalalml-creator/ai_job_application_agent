from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, JSON, Text
from sqlmodel import Field, SQLModel

from backend.app.models.base import new_id, utcnow


class FitAnalysisRow(SQLModel, table=True):
    __tablename__ = "fit_analyses"

    id: str = Field(default_factory=new_id, primary_key=True, max_length=36)
    user_id: str = Field(foreign_key="users.id", index=True, max_length=36)
    job_id: str = Field(foreign_key="jobs.id", index=True, max_length=36)
    search_run_id: Optional[str] = Field(default=None, foreign_key="search_runs.id", max_length=36)
    overall_score: float = Field(default=0.0)
    recommendation: str = Field(default="MAYBE", max_length=16, index=True)
    skill_match_score: float = Field(default=0.0)
    experience_match_score: float = Field(default=0.0)
    role_match_score: float = Field(default=0.0)
    education_match_score: float = Field(default=0.0)
    location_match_score: float = Field(default=0.0)
    matched_skills: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    missing_required_skills: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    missing_preferred_skills: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    strengths: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    gaps: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    experience_assessment: str = Field(default="", sa_column=Column(Text, nullable=False))
    reasoning: str = Field(default="", sa_column=Column(Text, nullable=False))
    critical_gaps: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
