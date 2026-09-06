from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from backend.app.schemas.profile import ProfileIn, ProfileOut


class InterviewQuestion(BaseModel):
    field: str
    ask: str


class InterviewInference(BaseModel):
    value: Any
    reason: str = ""


class InterviewState(BaseModel):
    confidence: dict[str, float] = Field(default_factory=dict)
    questions: list[InterviewQuestion] = Field(default_factory=list)
    inferences: dict[str, InterviewInference] = Field(default_factory=dict)
    question: str | None = None
    question_field: str | None = None
    resolved_fields: list[str] = Field(default_factory=list)
    inferred_fields: list[str] = Field(default_factory=list)
    done: bool = False


class ResumeUploadOut(BaseModel):
    profile: ProfileOut
    interview: InterviewState


class ProfileChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ProfileChatIn(BaseModel):
    action: Literal["answer", "skip", "confirm"] = "answer"
    message: str = ""
    messages: list[ProfileChatMessage] = Field(default_factory=list)
    profile: ProfileIn | None = None
    interview: InterviewState | None = None


class ProfileChatOut(BaseModel):
    profile: ProfileOut
    interview: InterviewState
    assistant_message: str
