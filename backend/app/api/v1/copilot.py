from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import ProfileChatIn, ProfileChatOut
from backend.app.services import copilot_service

router = APIRouter(prefix="/api/profile", tags=["copilot"])


@router.post("/chat", response_model=ProfileChatOut)
def chat_profile(
    payload: ProfileChatIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return copilot_service.chat(ProfileRepository(session), user.id, payload)
