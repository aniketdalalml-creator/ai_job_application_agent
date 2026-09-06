from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlmodel import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.schemas import LoginIn, RegisterIn, UserOut
from backend.app.services import auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, response: Response, session: Session = Depends(get_session)):
    return auth_service.register(session, payload, response)


@router.post("/login", response_model=UserOut)
def login(payload: LoginIn, response: Response, session: Session = Depends(get_session)):
    return auth_service.login(session, payload, response)


@router.post("/logout")
def logout(response: Response):
    return auth_service.logout(response)
