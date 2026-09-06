from __future__ import annotations

from sqlmodel import Session, select

from backend.app.models import Application


class ApplicationRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, application_id: str) -> Application | None:
        return self.session.get(Application, application_id)

    def list_for_user(self, user_id: str) -> list[Application]:
        return list(
            self.session.exec(
                select(Application).where(Application.user_id == user_id).order_by(Application.updated_at.desc())
            ).all()
        )

    def get_for_job(self, user_id: str, job_id: str) -> Application | None:
        return self.session.exec(
            select(Application).where(Application.user_id == user_id, Application.job_id == job_id)
        ).first()

    def add(self, application: Application) -> Application:
        self.session.add(application)
        return application
