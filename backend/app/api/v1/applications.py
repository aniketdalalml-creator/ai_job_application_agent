from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.application_repository import ApplicationRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.match_repository import MatchRepository
from backend.app.schemas import ApplicationPatch
from backend.app.services import application_service

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("")
def list_applications(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return application_service.list_applications(
        ApplicationRepository(session), JobRepository(session), MatchRepository(session), user
    )


@router.get("/{application_id}")
def get_application(
    application_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return application_service.get_application(
        ApplicationRepository(session), JobRepository(session), MatchRepository(session), user, application_id
    )


@router.patch("/{application_id}")
def patch_application(
    application_id: str,
    payload: ApplicationPatch,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return application_service.patch_application(
        ApplicationRepository(session),
        JobRepository(session),
        MatchRepository(session),
        user,
        application_id,
        payload,
    )


@router.get("/{application_id}/events")
async def application_events(
    application_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    application_service.owned(ApplicationRepository(session).get(application_id), user)

    async def stream():
        cursor = 0
        while True:
            with Session(session.bind) as inner:
                current = ApplicationRepository(inner).get(application_id)
                if not current:
                    break
                events = current.events or []
                while cursor < len(events):
                    yield f"data: {json.dumps(events[cursor])}\n\n"
                    cursor += 1
                if current.status in {"ready", "failed"}:
                    yield f"data: {json.dumps({'type': 'run_finished', 'status': current.status, 'error': current.error})}\n\n"
                    break
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream")
