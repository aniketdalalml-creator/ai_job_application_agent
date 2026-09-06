from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.application_repository import ApplicationRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.match_repository import MatchRepository
from backend.app.schemas import ManualJobIn
from backend.app.services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("")
def list_jobs(
    recommendation: str | None = None,
    min_score: float | None = Query(default=None),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return job_service.list_jobs(
        JobRepository(session),
        MatchRepository(session),
        ApplicationRepository(session),
        user,
        recommendation,
        min_score,
    )


@router.get("/{job_id}")
def get_job(job_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return job_service.get_job(JobRepository(session), MatchRepository(session), ApplicationRepository(session), user, job_id)


@router.post("/manual", status_code=201)
def create_manual_job(
    payload: ManualJobIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return job_service.create_manual_job(JobRepository(session), user, payload)


@router.post("/{job_id}/prepare", status_code=202)
def prepare_job(
    job_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return job_service.prepare_job(JobRepository(session), ApplicationRepository(session), user, job_id)
