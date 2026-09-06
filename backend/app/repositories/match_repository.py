from __future__ import annotations

from sqlmodel import Session, select

from backend.app.models import FitAnalysisRow


class MatchRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def latest_for_user(self, user_id: str) -> dict[str, FitAnalysisRow]:
        rows = self.session.exec(
            select(FitAnalysisRow)
            .where(FitAnalysisRow.user_id == user_id)
            .order_by(FitAnalysisRow.created_at.desc())
        ).all()
        latest: dict[str, FitAnalysisRow] = {}
        for row in rows:
            latest.setdefault(row.job_id, row)
        return latest

    def latest_for_job(self, user_id: str, job_id: str) -> FitAnalysisRow | None:
        return self.session.exec(
            select(FitAnalysisRow)
            .where(FitAnalysisRow.user_id == user_id, FitAnalysisRow.job_id == job_id)
            .order_by(FitAnalysisRow.created_at.desc())
        ).first()
