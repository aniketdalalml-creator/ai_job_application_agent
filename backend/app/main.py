from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app import models as _models  # noqa: F401 — register SQLModel tables
from backend.app.api.router import api_router
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.db.session import init_db
from backend.app.workers.queue import start_worker


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    start_worker()
    yield


app = FastAPI(title="CareerPilot", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


@app.get("/api/health")
def health() -> dict:
    settings = get_settings()
    return {
        "ok": True,
        "service": "careerpilot",
        "groq_model": settings.groq_model,
        "job_provider": settings.job_provider,
        "apify_configured": bool(settings.apify_token),
    }


frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
