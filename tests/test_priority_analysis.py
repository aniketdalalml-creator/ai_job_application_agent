"""Contract tests for application priority analysis (no scoring logic)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from job_agent.models import PriorityAnalysis, PriorityLevel, PriorityRanking, PriorityRecommendation

VALID = {
    "job_id": "job-1",
    "application_id": "app-1",
    "priority_score": 82,
    "priority_level": "HIGH",
    "fit_score": 74,
    "role_alignment_score": 80,
    "skill_strength_score": 70,
    "experience_score": 65,
    "application_effort_score": 40,
    "preference_score": 90,
    "reasons": ["Strong title match"],
    "risks": ["Visa unclear"],
    "recommendation": "APPLY_FIRST",
}

SCORE_FIELDS = (
    "priority_score",
    "fit_score",
    "role_alignment_score",
    "skill_strength_score",
    "experience_score",
    "application_effort_score",
    "preference_score",
)


def test_valid_priority_analysis() -> None:
    analysis = PriorityAnalysis.model_validate(VALID)
    assert analysis.priority_score == 82
    assert analysis.priority_level is PriorityLevel.HIGH
    assert analysis.recommendation is PriorityRecommendation.APPLY_FIRST
    assert analysis.fit_score == 74
    assert analysis.reasons == ["Strong title match"]
    assert analysis.risks == ["Visa unclear"]
    assert analysis.job_id == "job-1"


@pytest.mark.parametrize("score", [0, 100])
def test_score_boundaries_accepted(score: int) -> None:
    payload = {**VALID, **dict.fromkeys(SCORE_FIELDS, score)}
    analysis = PriorityAnalysis.model_validate(payload)
    for field in SCORE_FIELDS:
        assert getattr(analysis, field) == score


@pytest.mark.parametrize("score", [-0.1, -1, 100.1, 101])
@pytest.mark.parametrize("field", SCORE_FIELDS)
def test_invalid_scores_rejected(field: str, score: float) -> None:
    with pytest.raises(ValidationError):
        PriorityAnalysis.model_validate({**VALID, field: score})


@pytest.mark.parametrize("value", ["high", "URGENT", "", None, 1])
def test_invalid_priority_level_rejected(value: object) -> None:
    with pytest.raises(ValidationError):
        PriorityAnalysis.model_validate({**VALID, "priority_level": value})


@pytest.mark.parametrize("value", ["SKIP", "APPLY_NOW", "", None])
def test_invalid_recommendation_rejected(value: object) -> None:
    with pytest.raises(ValidationError):
        PriorityAnalysis.model_validate({**VALID, "recommendation": value})


def test_missing_required_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        PriorityAnalysis.model_validate({"priority_level": "HIGH", "recommendation": "APPLY"})


def test_empty_reasons_and_risks_default() -> None:
    payload = {k: v for k, v in VALID.items() if k not in {"reasons", "risks"}}
    analysis = PriorityAnalysis.model_validate(payload)
    assert analysis.reasons == []
    assert analysis.risks == []


def test_none_reasons_and_risks_become_empty() -> None:
    analysis = PriorityAnalysis.model_validate({**VALID, "reasons": None, "risks": None})
    assert analysis.reasons == []
    assert analysis.risks == []


def test_ranking_holds_many_analyses() -> None:
    first = PriorityAnalysis.model_validate(VALID)
    second = PriorityAnalysis.model_validate({**VALID, "job_id": "job-2", "priority_score": 40, "priority_level": "LOW", "recommendation": "DEPRIORITIZE"})
    ranking = PriorityRanking(analyses=[first, second])
    assert len(ranking.analyses) == 2
    assert ranking.analyses[1].job_id == "job-2"
