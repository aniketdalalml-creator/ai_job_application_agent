from __future__ import annotations

from fastapi import Response
from sqlmodel import Session

from backend.app.core.config import get_settings
from backend.app.core.exceptions import ConflictError, UnauthorizedError
from backend.app.core.security import COOKIE_NAME, create_access_token, hash_password, verify_password
from backend.app.models import Profile, User
from backend.app.repositories.user_repository import UserRepository
from backend.app.schemas import LoginIn, RegisterIn, UserOut


def user_out(user: User) -> UserOut:
    return UserOut(id=user.id, email=user.email, name=user.name, created_at=user.created_at)


def set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.jwt_expire_days * 24 * 60 * 60,
        path="/",
    )


def register(session: Session, payload: RegisterIn, response: Response) -> UserOut:
    users = UserRepository(session)
    email = payload.email.lower().strip()
    if users.get_by_email(email):
        raise ConflictError("Email already registered")
    user = User(email=email, password_hash=hash_password(payload.password), name=payload.name.strip())
    users.add(user)
    session.flush()
    session.add(Profile(user_id=user.id))
    session.commit()
    session.refresh(user)
    set_session_cookie(response, create_access_token(user.id))
    return user_out(user)


def login(session: Session, payload: LoginIn, response: Response) -> UserOut:
    users = UserRepository(session)
    email = payload.email.lower().strip()
    user = users.get_by_email(email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    set_session_cookie(response, create_access_token(user.id))
    return user_out(user)


def logout(response: Response) -> dict:
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"ok": True}
