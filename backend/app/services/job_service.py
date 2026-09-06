from __future__ import annotations

import uuid

from backend.app.core.exceptions import NotFoundError
from backend.app.models import Application, Job, User
from backend.app.repositories.application_repository import ApplicationRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.match_repository import MatchRepository
from backend.app.schemas import ManualJobIn
from backend.app.workers.queue import enqueue


def _serialize_job(job: Job, fit, application: Application | None) -> dict:
    return {
        "id": job.id,
        "source": job.source,
        "external_id": job.external_id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "description": job.description,
        "url": job.url,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "application_id": application.id if application else None,
        "application_status": application.status if application else None,
        "fit": None
        if not fit
        else {
            "overall_score": fit.overall_score,
            "recommendation": fit.recommendation,
            "skill_match_score": fit.skill_match_score,
            "experience_match_score": fit.experience_match_score,
            "role_match_score": fit.role_match_score,
            "education_match_score": fit.education_match_score,
            "location_match_score": fit.location_match_score,
            "matched_skills": fit.matched_skills,
            "missing_required_skills": fit.missing_required_skills,
            "missing_preferred_skills": fit.missing_preferred_skills,
            "strengths": fit.strengths,
            "gaps": fit.gaps,
            "reasoning": fit.reasoning,
            "experience_assessment": fit.experience_assessment,
            "critical_gaps": fit.critical_gaps,
        },
    }


def list_jobs(
    jobs: JobRepository,
    matches: MatchRepository,
    applications: ApplicationRepository,
    user: User,
    recommendation: str | None = None,
    min_score: float | None = None,
) -> list[dict]:
    rows = jobs.list_for_user(user.id)
    fits = matches.latest_for_user(user.id)
    app_by_job = {item.job_id: item for item in applications.list_for_user(user.id)}
    payload = [_serialize_job(job, fits.get(job.id), app_by_job.get(job.id)) for job in rows]
    if recommendation:
        payload = [item for item in payload if (item["fit"] or {}).get("recommendation") == recommendation.upper()]
    if min_score is not None:
        payload = [item for item in payload if ((item["fit"] or {}).get("overall_score") or 0) >= min_score]
    payload.sort(key=lambda item: ((item["fit"] or {}).get("overall_score") or 0), reverse=True)
    return payload


def get_job(jobs: JobRepository, matches: MatchRepository, applications: ApplicationRepository, user: User, job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job or job.user_id != user.id:
        raise NotFoundError("Job not found")
    return _serialize_job(job, matches.latest_for_job(user.id, job.id), applications.get_for_job(user.id, job.id))


def create_manual_job(jobs: JobRepository, user: User, payload: ManualJobIn) -> dict:
    job = Job(
        user_id=user.id,
        source="manual",
        external_id=f"manual-{uuid.uuid4()}",
        title=payload.title.strip() or "Pasted role",
        company=payload.company_name.strip(),
        location=payload.location.strip(),
        description=payload.job_description.strip(),
        url="",
        raw={},
    )
    jobs.add(job)
    jobs.session.commit()
    jobs.session.refresh(job)
    enqueue("fit", job.id)
    return {"id": job.id, "status": "scoring"}


def prepare_job(jobs: JobRepository, applications: ApplicationRepository, user: User, job_id: str) -> dict:
    job = jobs.get(job_id)
    if not job or job.user_id != user.id:
        raise NotFoundError("Job not found")
    application = applications.get_for_job(user.id, job.id)
    if not application:
        application = Application(user_id=user.id, job_id=job.id, status="generating", events=[])
    else:
        application.status = "generating"
        application.error = ""
        application.events = []
    applications.add(application)
    applications.session.commit()
    applications.session.refresh(application)
    enqueue("prepare", application.id)
    return {"id": application.id, "status": application.status, "job_id": job.id}
