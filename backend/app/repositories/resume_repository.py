"""Resume text is stored on Profile today. This adapter keeps the seam for later files."""

from __future__ import annotations

from backend.app.repositories.profile_repository import ProfileRepository


class ResumeRepository(ProfileRepository):
    pass
