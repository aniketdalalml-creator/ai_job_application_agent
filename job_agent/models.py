from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class CompanyResearch(BaseModel):
    """Structured handoff from Researcher → Writer."""

    companyName: str
    companyFacts: list[str] = Field(default_factory=list)
    roleRequirements: list[str] = Field(default_factory=list)
    cultureSignals: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)

    @field_validator(
        "companyFacts",
        "roleRequirements",
        "cultureSignals",
        "sources",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)


class Critique(BaseModel):
    """Self-critique of a cover letter draft."""

    hasIssues: bool = False
    issues: list[str] = Field(default_factory=list)
    unsupportedClaims: list[str] = Field(default_factory=list)
    missingAlignment: list[str] = Field(default_factory=list)

    @field_validator(
        "issues",
        "unsupportedClaims",
        "missingAlignment",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)


class ApplicationMaterials(BaseModel):
    """Tailored cover letter and resume bullets."""

    coverLetter: str
    resumeBullets: list[str] = Field(default_factory=list)

    @field_validator("resumeBullets", mode="before")
    @classmethod
    def _coerce_bullets(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)


class PipelineResult(BaseModel):
    """Final output of the cover-letter pipeline."""

    research: CompanyResearch
    draft: ApplicationMaterials
    critique: Critique
    final_materials: ApplicationMaterials
    revised: bool = False
