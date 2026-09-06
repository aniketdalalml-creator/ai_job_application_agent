from __future__ import annotations

from sqlmodel import Session, select

from backend.app.models import User


class UserRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, user_id: str) -> User | None:
        return self.session.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.session.exec(select(User).where(User.email == email)).first()

    def add(self, user: User) -> User:
        self.session.add(user)
        return user
