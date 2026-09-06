from __future__ import annotations

from datetime import datetime

from backend.app.core.exceptions import NotFoundError
from backend.app.models import Application, FitAnalysisRow, Job, User
from backend.app.repositories.application_repository import ApplicationRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.match_repository import MatchRepository
from backend.app.schemas import ApplicationPatch


def _serialize_fit(fit: FitAnalysisRow | None) -> dict | None:
    if not fit:
        return None
    return {
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
    }


def serialize(application: Application, job: Job | None, fit: FitAnalysisRow | None = None) -> dict:
    return {
        "id": application.id,
        "job_id": application.job_id,
        "status": application.status,
        "cover_letter": application.cover_letter,
        "resume_bullets": application.resume_bullets,
        "research": application.research,
        "critique": application.critique,
        "revised": application.revised,
        "notes": application.notes,
        "error": application.error,
        "events": application.events,
        "created_at": application.created_at.isoformat() if application.created_at else None,
        "updated_at": application.updated_at.isoformat() if application.updated_at else None,
        "applied_at": application.applied_at.isoformat() if application.applied_at else None,
        "company": job.company if job else "",
        "title": job.title if job else "",
        "job_url": job.url if job else "",
        "fit": _serialize_fit(fit),
    }


def owned(application: Application | None, user: User) -> Application:
    if not application or application.user_id != user.id:
        raise NotFoundError("Application not found")
    return application


def list_applications(
    applications: ApplicationRepository,
    jobs: JobRepository,
    matches: MatchRepository,
    user: User,
) -> list[dict]:
    items = applications.list_for_user(user.id)
    job_map = {job.id: job for job in jobs.list_for_user(user.id)}
    fits = matches.latest_for_user(user.id)
    return [serialize(item, job_map.get(item.job_id), fits.get(item.job_id)) for item in items]


def get_application(
    applications: ApplicationRepository,
    jobs: JobRepository,
    matches: MatchRepository,
    user: User,
    application_id: str,
) -> dict:
    application = owned(applications.get(application_id), user)
    return serialize(
        application,
        jobs.get(application.job_id),
        matches.latest_for_job(user.id, application.job_id),
    )


def patch_application(
    applications: ApplicationRepository,
    jobs: JobRepository,
    matches: MatchRepository,
    user: User,
    application_id: str,
    payload: ApplicationPatch,
) -> dict:
    application = owned(applications.get(application_id), user)
    if payload.status:
        application.status = payload.status
        if payload.status == "applied" and not application.applied_at:
            application.applied_at = datetime.utcnow()
    if payload.notes is not None:
        application.notes = payload.notes
    application.updated_at = datetime.utcnow()
    applications.add(application)
    applications.session.commit()
    applications.session.refresh(application)
    return serialize(
        application,
        jobs.get(application.job_id),
        matches.latest_for_job(user.id, application.job_id),
    )
