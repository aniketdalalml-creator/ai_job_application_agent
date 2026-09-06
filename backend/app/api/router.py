from __future__ import annotations

from fastapi import APIRouter

from backend.app.api.v1 import (
    applications,
    auth,
    copilot,
    dashboard,
    jobs,
    matches,
    profiles,
    resumes,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(profiles.router)
api_router.include_router(resumes.router)
api_router.include_router(copilot.router)
api_router.include_router(matches.router)
api_router.include_router(jobs.router)
api_router.include_router(applications.router)
api_router.include_router(dashboard.router)
