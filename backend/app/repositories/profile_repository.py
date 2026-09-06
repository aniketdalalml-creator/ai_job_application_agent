from __future__ import annotations

from sqlmodel import Session, select

from backend.app.models import Profile


class ProfileRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_user(self, user_id: str) -> Profile | None:
        return self.session.exec(select(Profile).where(Profile.user_id == user_id)).first()

    def add(self, profile: Profile) -> Profile:
        self.session.add(profile)
        return profile

    def ensure(self, user_id: str) -> Profile:
        profile = self.get_by_user(user_id)
        if profile:
            return profile
        profile = Profile(user_id=user_id)
        self.session.add(profile)
        self.session.commit()
        self.session.refresh(profile)
        return profile
