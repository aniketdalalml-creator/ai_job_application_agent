from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import ResumeUploadOut
from backend.app.services import resume_service

router = APIRouter(prefix="/api/profile", tags=["resumes"])


@router.post("/resume", response_model=ResumeUploadOut)
async def upload_resume(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    data = await file.read()
    return resume_service.upload_resume(ProfileRepository(session), user.id, file.filename or "resume.txt", data)
