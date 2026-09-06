from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.services.dashboard_service import build_insights

router = APIRouter(prefix="/api/insights", tags=["dashboard"])


@router.get("")
def insights(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return build_insights(session, user.id)
