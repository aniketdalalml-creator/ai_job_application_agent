from __future__ import annotations

from backend.app.core.exceptions import AppError, NotFoundError
from backend.app.models import SearchRun, User
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import SearchStartOut
from backend.app.workers.queue import enqueue


def queue_search(jobs: JobRepository, profile_repo: ProfileRepository, user: User) -> SearchRun:
    profile = profile_repo.get_by_user(user.id)
    if not profile:
        raise AppError("Create a profile first")
    query = ", ".join(profile.target_titles or []) or "software engineer"
    run = SearchRun(
        user_id=user.id,
        status="queued",
        query=query,
        filters={
            "locations": profile.locations or [],
            "country": profile.country,
            "work_mode": profile.work_mode,
        },
        events=[],
    )
    jobs.add_search(run)
    jobs.session.commit()
    jobs.session.refresh(run)
    enqueue("search", run.id)
    return run


def start_search(jobs: JobRepository, profile_repo: ProfileRepository, user: User) -> SearchStartOut:
    run = queue_search(jobs, profile_repo, user)
    return SearchStartOut(id=run.id, status=run.status)


def serialize_search(run: SearchRun) -> dict:
    return {
        "id": run.id,
        "status": run.status,
        "query": run.query,
        "filters": run.filters,
        "result_count": run.result_count,
        "avg_fit": run.avg_fit,
        "error": run.error,
        "events": run.events,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


def get_search(jobs: JobRepository, user: User, search_id: str) -> SearchRun:
    run = jobs.get_search(search_id)
    if not run or run.user_id != user.id:
        raise NotFoundError("Search not found")
    return run
