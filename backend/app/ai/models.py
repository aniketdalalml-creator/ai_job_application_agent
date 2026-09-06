from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


# ──────────────────────────────────────────────────────
# Pipeline models (Researcher → Writer)
# ──────────────────────────────────────────────────────


class CompanyResearch(BaseModel):
    """Structured research handoff from the Researcher agent."""

    companyName: str = ""
    companyFacts: list[str] = Field(default_factory=list)
    roleRequirements: list[str] = Field(default_factory=list)
    cultureSignals: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    researchNotes: str = ""


class ApplicationMaterials(BaseModel):
    coverLetter: str = ""
    resumeBullets: list[str] = Field(default_factory=list)


class Critique(BaseModel):
    hasIssues: bool = False
    issues: list[str] = Field(default_factory=list)
    unsupportedClaims: list[str] = Field(default_factory=list)
    missingAlignment: list[str] = Field(default_factory=list)


class PipelineResult(BaseModel):
    research: CompanyResearch
    draft: ApplicationMaterials
    critique: Critique
    final_materials: ApplicationMaterials
    revised: bool = False


# ──────────────────────────────────────────────────────
# Candidate + job search
# ──────────────────────────────────────────────────────


class CandidateProfile(BaseModel):
    """In-memory view of the seeker used by search and fit scoring."""

    name: str = ""
    resume_text: str = ""
    target_titles: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    years_experience: float = 0.0
    locations: list[str] = Field(default_factory=list)
    work_mode: Literal["on-site", "remote", "hybrid"] = "hybrid"
    country: str = "us"


class NormalizedJob(BaseModel):
    source: str = "adzuna"
    external_id: str
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    url: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


# ──────────────────────────────────────────────────────
# Job requirements extracted from a job description
# ──────────────────────────────────────────────────────


class JobRequirements(BaseModel):
    """Structured extraction of job description requirements."""

    title: str = ""
    location: str = ""
    work_mode: Literal["on-site", "remote", "hybrid"] = "on-site"
    education_requirements: list[str] = Field(default_factory=list)
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    minimum_experience_months: int = 0
    years_experience_required: float = 0.0
    responsibilities: list[str] = Field(default_factory=list)

    @field_validator(
        "education_requirements",
        "required_skills",
        "preferred_skills",
        "responsibilities",
        mode="before",
    )
    @classmethod
    def _coerce_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return list(value)


# ──────────────────────────────────────────────────────
# Fit analysis result — candidate vs job
# ──────────────────────────────────────────────────────


class FitScoreBreakdown(BaseModel):
    """Per-category scores for the overall fit score."""

    skills: float = 0.0
    experience: float = 0.0
    role_alignment: float = 0.0
    education: float = 0.0
    location: float = 0.0
    other: float = 0.0


class FitAnalysis(BaseModel):
    """Result of comparing a candidate to a job."""

    overall_score: float = Field(default=0.0, ge=0, le=100)
    recommendation: Literal["APPLY", "MAYBE", "SKIP"] = "MAYBE"
    skill_match_score: float = Field(default=0.0, ge=0, le=100)
    experience_match_score: float = Field(default=0.0, ge=0, le=100)
    role_match_score: float = Field(default=0.0, ge=0, le=100)
    education_match_score: float = Field(default=0.0, ge=0, le=100)
    location_match_score: float = Field(default=0.0, ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    missing_required_skills: list[str] = Field(default_factory=list)
    missing_preferred_skills: list[str] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    experience_assessment: str = ""
    reasoning: str = ""

    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "skills": 0.4,
            "experience": 0.2,
            "role_alignment": 0.15,
            "education": 0.1,
            "location": 0.1,
            "other": 0.05,
        }
    )
    critical_gaps: list[str] = Field(default_factory=list)


class FitAnalysisWeights(BaseModel):
    """Configurable weights for the fit scoring system."""

    skills: float = 0.4
    experience: float = 0.2
    role_alignment: float = 0.15
    education: float = 0.1
    location: float = 0.1
    other: float = 0.05

    @field_validator("*")
    @classmethod
    def _check_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Weights must be non-negative")
        return v

    @property
    def total(self) -> float:
        return (
            self.skills
            + self.experience
            + self.role_alignment
            + self.education
            + self.location
            + self.other
        )


RecommendationTier = Literal["APPLY", "MAYBE", "SKIP"]

TIER_THRESHOLDS: dict[str, tuple[int, int]] = {
    "APPLY": (75, 100),
    "MAYBE": (55, 74),
    "SKIP": (0, 54),
}


def get_tier(score: float) -> RecommendationTier:
    """Determine recommendation tier from a 0–100 score."""
    if score >= 75:
        return "APPLY"
    if score >= 55:
        return "MAYBE"
    return "SKIP"


# ──────────────────────────────────────────────────────
# Application priority — contract only (no scoring yet)
# ──────────────────────────────────────────────────────


class PriorityLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityRecommendation(str, Enum):
    APPLY_FIRST = "APPLY_FIRST"
    APPLY = "APPLY"
    CONSIDER = "CONSIDER"
    DEPRIORITIZE = "DEPRIORITIZE"


def _score_field() -> Any:
    return Field(..., ge=0, le=100)


class PriorityAnalysis(BaseModel):
    """Priority of one job or application. Later used to rank many side by side."""

    job_id: str | None = None
    application_id: str | None = None
    priority_score: float = _score_field()
    priority_level: PriorityLevel
    fit_score: float = _score_field()
    role_alignment_score: float = _score_field()
    skill_strength_score: float = _score_field()
    experience_score: float = _score_field()
    application_effort_score: float = _score_field()
    preference_score: float = _score_field()
    reasons: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    recommendation: PriorityRecommendation

    @field_validator("reasons", "risks", mode="before")
    @classmethod
    def _coerce_text_list(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            text = value.strip()
            return [text] if text else []
        return [str(item).strip() for item in value if str(item).strip()]


class PriorityRanking(BaseModel):
    """Batch of priority analyses for comparing many jobs later."""

    analyses: list[PriorityAnalysis] = Field(default_factory=list)
