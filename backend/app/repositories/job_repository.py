from __future__ import annotations

from sqlmodel import Session, select

from backend.app.models import Job, SearchRun


class JobRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, job_id: str) -> Job | None:
        return self.session.get(Job, job_id)

    def list_for_user(self, user_id: str) -> list[Job]:
        return list(self.session.exec(select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())).all())

    def add(self, job: Job) -> Job:
        self.session.add(job)
        return job

    def get_search(self, search_id: str) -> SearchRun | None:
        return self.session.get(SearchRun, search_id)

    def list_searches(self, user_id: str) -> list[SearchRun]:
        return list(
            self.session.exec(select(SearchRun).where(SearchRun.user_id == user_id).order_by(SearchRun.created_at.desc())).all()
        )

    def add_search(self, run: SearchRun) -> SearchRun:
        self.session.add(run)
        return run
