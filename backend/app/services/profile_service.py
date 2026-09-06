from __future__ import annotations

from datetime import datetime

from backend.app.core.exceptions import AppError
from backend.app.models import Profile
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import ProfileIn


def apply_snapshot(profile: Profile, snapshot: dict) -> None:
    profile.resume_text = snapshot.get("resume_text", profile.resume_text)
    profile.target_titles = [item.strip() for item in snapshot.get("target_titles") or [] if str(item).strip()]
    profile.skills = [item.strip() for item in snapshot.get("skills") or [] if str(item).strip()]
    profile.years_experience = max(0.0, float(snapshot.get("years_experience") or 0))
    profile.locations = [item.strip() for item in snapshot.get("locations") or [] if str(item).strip()]
    work_mode = snapshot.get("work_mode")
    if work_mode not in {"on-site", "remote", "hybrid"}:
        raise AppError("Invalid work_mode")
    profile.work_mode = work_mode
    profile.country = (snapshot.get("country") or "us").strip().lower()[:2]
    profile.updated_at = datetime.utcnow()


def get_or_create(repo: ProfileRepository, user_id: str) -> Profile:
    return repo.ensure(user_id)


def update_profile(repo: ProfileRepository, user_id: str, payload: ProfileIn) -> Profile:
    profile = repo.ensure(user_id)
    apply_snapshot(profile, payload.model_dump())
    repo.add(profile)
    repo.session.commit()
    repo.session.refresh(profile)
    return profile
