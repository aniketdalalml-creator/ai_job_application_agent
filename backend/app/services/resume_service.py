from __future__ import annotations

from backend.app.ai.profile_interview import build_interview, interview_from_profile
from backend.app.ai.resume_parser import MAX_RESUME_BYTES, extract_text, parse_resume_profile
from backend.app.core.exceptions import AppError
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import InterviewState, ProfileOut, ResumeUploadOut
from backend.app.services.profile_service import apply_snapshot


def upload_resume(repo: ProfileRepository, user_id: str, filename: str, data: bytes) -> ResumeUploadOut:
    if not data:
        raise AppError("The uploaded file is empty.")
    if len(data) > MAX_RESUME_BYTES:
        raise AppError("Resume must be 2 MB or smaller.")
    try:
        resume_text = extract_text(filename, data)
    except ValueError as exc:
        raise AppError(str(exc)) from exc

    parsed = parse_resume_profile(resume_text)
    profile = repo.ensure(user_id)
    if not parsed.get("country"):
        parsed["country"] = (profile.country or "us").strip().lower()[:2] or "us"
    prior = parsed.get("interview") or {}
    parsed["interview"] = build_interview(
        parsed,
        confidence=prior.get("confidence"),
        questions=prior.get("questions"),
        inferences=prior.get("inferences"),
    )
    apply_snapshot(profile, parsed)
    repo.add(profile)
    repo.session.commit()
    repo.session.refresh(profile)
    interview = parsed.get("interview") or interview_from_profile(profile)
    return ResumeUploadOut(
        profile=ProfileOut.model_validate(profile),
        interview=InterviewState.model_validate(interview),
    )
