"""Extract job requirements and score a candidate against a posting."""

from __future__ import annotations

import re

from backend.app.integrations.llm import chat, extract_json
from backend.app.ai.models import (
    CandidateProfile,
    FitAnalysis,
    FitAnalysisWeights,
    JobRequirements,
    RecommendationTier,
    get_tier,
)

__all__ = [
    "FitAnalysis",
    "FitAnalysisWeights",
    "JobRequirements",
    "RecommendationTier",
    "analyze_fit",
    "extract_requirements",
    "get_tier",
    "score_fit",
]

EXTRACT_SYSTEM = """You extract structured hiring requirements from a job description.

Return JSON with this exact shape:
{
  "title": string,
  "location": string,
  "work_mode": "on-site" | "remote" | "hybrid",
  "education_requirements": [string, ...],
  "required_skills": [string, ...],
  "preferred_skills": [string, ...],
  "minimum_experience_months": number,
  "years_experience_required": number,
  "responsibilities": [string, ...]
}

Rules:
- required_skills: concrete tools/skills that are must-haves (4-12 items)
- preferred_skills: nice-to-haves only
- years_experience_required: 0 if unspecified
- work_mode: infer from the text; default hybrid if unclear
- Do not invent requirements that are not in the description
- Return only JSON"""


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9+#]+", " ", value.lower()).strip()


def _tokens(value: str) -> set[str]:
    return {part for part in _norm(value).split() if len(part) > 1}


def _skill_hit(skill: str, haystack: str) -> bool:
    needle = _norm(skill)
    if not needle:
        return False
    blob = _norm(haystack)
    if needle in blob:
        return True
    parts = needle.split()
    return len(parts) > 1 and all(part in blob for part in parts)


def extract_requirements(job_title: str, job_description: str) -> JobRequirements:
    """LLM extraction of structured requirements, with a keyword fallback."""
    try:
        raw = chat(
            [
                {"role": "system", "content": EXTRACT_SYSTEM},
                {
                    "role": "user",
                    "content": f"Title: {job_title}\n\nJob description:\n{job_description}",
                },
            ],
            temperature=0.1,
            json_mode=True,
        )
        data = extract_json(raw)
        if not data.get("title"):
            data["title"] = job_title
        return JobRequirements.model_validate(data)
    except Exception:  # noqa: BLE001 — keep search usable if the LLM is down
        return _fallback_requirements(job_title, job_description)


def _fallback_requirements(job_title: str, job_description: str) -> JobRequirements:
    text = job_description.lower()
    if "remote" in text:
        mode = "remote"
    elif "hybrid" in text:
        mode = "hybrid"
    else:
        mode = "on-site"
    years = 0.0
    match = re.search(r"(\d+)\+?\s*(?:years|yrs)", text)
    if match:
        years = float(match.group(1))
    return JobRequirements(
        title=job_title,
        work_mode=mode,
        years_experience_required=years,
        minimum_experience_months=int(years * 12),
        required_skills=[],
        preferred_skills=[],
    )


def _score_skills(
    required: list[str],
    preferred: list[str],
    profile: CandidateProfile,
) -> tuple[float, list[str], list[str], list[str]]:
    haystack = " ".join([profile.resume_text, *profile.skills, *profile.target_titles])
    matched: list[str] = []
    missing_required: list[str] = []
    missing_preferred: list[str] = []

    for skill in required:
        if _skill_hit(skill, haystack):
            matched.append(skill)
        else:
            missing_required.append(skill)
    for skill in preferred:
        if _skill_hit(skill, haystack):
            if skill not in matched:
                matched.append(skill)
        else:
            missing_preferred.append(skill)

    if required:
        required_score = 100.0 * len([s for s in required if s in matched]) / len(required)
    else:
        required_score = 70.0 if profile.skills or profile.resume_text else 40.0

    if preferred:
        preferred_score = 100.0 * len([s for s in preferred if s in matched]) / len(preferred)
        score = required_score * 0.8 + preferred_score * 0.2
    else:
        score = required_score
    return min(100.0, score), matched, missing_required, missing_preferred


def _score_experience(required_years: float, profile: CandidateProfile) -> tuple[float, str]:
    have = profile.years_experience
    if required_years <= 0:
        return (80.0 if have > 0 else 60.0), "No explicit experience minimum."
    if have >= required_years:
        return 100.0, f"{have:g} years meets the {required_years:g}+ year requirement."
    ratio = have / required_years
    score = max(20.0, min(90.0, ratio * 100.0))
    return score, f"{have:g} years vs {required_years:g} years requested."


def _score_role(job_title: str, profile: CandidateProfile, requirements: JobRequirements) -> float:
    title = _norm(job_title or requirements.title)
    candidates = [_norm(t) for t in profile.target_titles if t.strip()]
    if title and any(title in target or target in title for target in candidates):
        return 95.0
    title_tokens = _tokens(title)
    target_tokens: set[str] = set()
    for item in candidates:
        target_tokens |= _tokens(item)
    if title_tokens and target_tokens:
        overlap = title_tokens & target_tokens
        return min(100.0, 40.0 + 60.0 * len(overlap) / max(len(title_tokens), 1))
    resume_tokens = _tokens(profile.resume_text[:2000])
    if title_tokens and resume_tokens:
        overlap = title_tokens & resume_tokens
        return min(85.0, 30.0 + 50.0 * len(overlap) / max(len(title_tokens), 1))
    return 50.0


def _score_education(requirements: JobRequirements, profile: CandidateProfile) -> float:
    if not requirements.education_requirements:
        return 80.0
    haystack = _norm(profile.resume_text)
    hits = 0
    for item in requirements.education_requirements:
        tokens = _tokens(item)
        if tokens and tokens <= set(haystack.split()):
            hits += 1
        elif any(token in haystack for token in tokens if len(token) > 3):
            hits += 1
    if "bachelor" in haystack or "master" in haystack or "degree" in haystack:
        hits = max(hits, 1)
    return min(100.0, 40.0 + 60.0 * hits / max(len(requirements.education_requirements), 1))


def _score_location(job_location: str, work_mode: str, profile: CandidateProfile) -> float:
    if work_mode == "remote" or profile.work_mode == "remote":
        return 95.0
    if not job_location:
        return 70.0
    job_norm = _norm(job_location)
    for loc in profile.locations:
        loc_norm = _norm(loc)
        if loc_norm and (loc_norm in job_norm or job_norm in loc_norm):
            return 100.0
    if profile.work_mode == "hybrid" and work_mode == "hybrid":
        return 75.0
    return 45.0


def score_fit(
    profile: CandidateProfile,
    job_title: str,
    job_location: str,
    requirements: JobRequirements,
    weights: FitAnalysisWeights | None = None,
) -> FitAnalysis:
    weights = weights or FitAnalysisWeights()
    total = weights.total or 1.0
    skill_score, matched, missing_req, missing_pref = _score_skills(
        requirements.required_skills,
        requirements.preferred_skills,
        profile,
    )
    exp_score, exp_note = _score_experience(requirements.years_experience_required, profile)
    role_score = _score_role(job_title, profile, requirements)
    edu_score = _score_education(requirements, profile)
    loc_score = _score_location(job_location or requirements.location, requirements.work_mode, profile)
    other_score = 70.0 if profile.resume_text.strip() else 40.0

    overall = (
        skill_score * weights.skills
        + exp_score * weights.experience
        + role_score * weights.role_alignment
        + edu_score * weights.education
        + loc_score * weights.location
        + other_score * weights.other
    ) / total
    overall = round(min(100.0, max(0.0, overall)), 1)
    tier = get_tier(overall)

    strengths: list[str] = []
    gaps: list[str] = []
    if matched:
        strengths.append(f"Matched skills: {', '.join(matched[:6])}")
    if role_score >= 75:
        strengths.append("Role title aligns with target search.")
    if exp_score >= 80:
        strengths.append(exp_note)
    if missing_req:
        gaps.append(f"Missing required skills: {', '.join(missing_req[:6])}")
    if exp_score < 55:
        gaps.append(exp_note)
    if loc_score < 55:
        gaps.append("Location / work-mode mismatch.")

    critical = [f"Required skill missing: {skill}" for skill in missing_req[:4]]
    if critical and overall >= 75:
        tier = "MAYBE"
        overall = min(overall, 74.0)

    reasoning = (
        f"{tier} at {overall:.0f}. Skills {skill_score:.0f}, experience {exp_score:.0f}, "
        f"role {role_score:.0f}. {exp_note}"
    )
    return FitAnalysis(
        overall_score=overall,
        recommendation=tier,
        skill_match_score=round(skill_score, 1),
        experience_match_score=round(exp_score, 1),
        role_match_score=round(role_score, 1),
        education_match_score=round(edu_score, 1),
        location_match_score=round(loc_score, 1),
        matched_skills=matched,
        missing_required_skills=missing_req,
        missing_preferred_skills=missing_pref,
        strengths=strengths,
        gaps=gaps,
        experience_assessment=exp_note,
        reasoning=reasoning,
        weights=weights.model_dump(),
        critical_gaps=critical,
    )


def analyze_fit(
    profile: CandidateProfile,
    job_title: str,
    job_description: str,
    job_location: str = "",
) -> FitAnalysis:
    """Extract requirements, then score the candidate against the job."""
    requirements = extract_requirements(job_title, job_description)
    return score_fit(profile, job_title, job_location, requirements)
