from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import SearchStartOut
from backend.app.services import matching_service

router = APIRouter(prefix="/api/searches", tags=["matches"])


@router.post("", response_model=SearchStartOut, status_code=202)
def start_search(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return matching_service.start_search(JobRepository(session), ProfileRepository(session), user)


@router.get("")
def list_searches(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return [matching_service.serialize_search(run) for run in JobRepository(session).list_searches(user.id)]


@router.get("/{search_id}")
def get_search(search_id: str, user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    run = matching_service.get_search(JobRepository(session), user, search_id)
    return matching_service.serialize_search(run)


@router.get("/{search_id}/events")
async def search_events(
    search_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    matching_service.get_search(JobRepository(session), user, search_id)

    async def stream():
        cursor = 0
        while True:
            with Session(session.bind) as inner:
                current = JobRepository(inner).get_search(search_id)
                if not current:
                    break
                events = current.events or []
                while cursor < len(events):
                    yield f"data: {json.dumps(events[cursor])}\n\n"
                    cursor += 1
                if current.status in {"completed", "failed"}:
                    yield f"data: {json.dumps({'type': 'run_finished', 'status': current.status, 'error': current.error})}\n\n"
                    break
            await asyncio.sleep(0.5)

    return StreamingResponse(stream(), media_type="text/event-stream")
