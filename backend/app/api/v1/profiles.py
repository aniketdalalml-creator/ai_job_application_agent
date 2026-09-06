from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import ProfileIn, ProfileOut
from backend.app.services import profile_service

router = APIRouter(prefix="/api/profile", tags=["profiles"])


@router.get("", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return profile_service.get_or_create(ProfileRepository(session), user.id)


@router.put("", response_model=ProfileOut)
def update_profile(
    payload: ProfileIn,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return profile_service.update_profile(ProfileRepository(session), user.id, payload)
