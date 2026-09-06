from __future__ import annotations

from datetime import datetime

from sqlalchemy import Column, DateTime
from sqlmodel import Field, SQLModel

from backend.app.models.base import new_id, utcnow


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=new_id, primary_key=True, max_length=36)
    email: str = Field(unique=True, index=True, max_length=255)
    password_hash: str = Field(max_length=255)
    name: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=utcnow, sa_column=Column(DateTime, nullable=False))
