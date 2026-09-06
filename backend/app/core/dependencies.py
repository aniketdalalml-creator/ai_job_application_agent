from __future__ import annotations

from fastapi import Cookie, Depends
from sqlmodel import Session

from backend.app.core.exceptions import UnauthorizedError
from backend.app.core.security import COOKIE_NAME, decode_access_token
from backend.app.db.session import get_session
from backend.app.models import User
from backend.app.repositories.user_repository import UserRepository


def get_current_user(
    session: Session = Depends(get_session),
    access_token: str | None = Cookie(default=None, alias=COOKIE_NAME),
) -> User:
    if not access_token:
        raise UnauthorizedError("Not authenticated")
    user_id = decode_access_token(access_token)
    if not user_id:
        raise UnauthorizedError("Invalid session")
    user = UserRepository(session).get(user_id)
    if not user:
        raise UnauthorizedError("User not found")
    return user
