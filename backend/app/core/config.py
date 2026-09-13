from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

from backend.app.integrations.llm.groq import resolve_groq_model

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(_PROJECT_ROOT / ".env", override=True)
load_dotenv()


def _csv(value: str, default: list[str] | None = None) -> list[str]:
    items = [part.strip() for part in (value or "").split(",") if part.strip()]
    return items or list(default or [])


def _int(name: str, default: int, *, min_value: int | None = None, max_value: int | None = None) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError:
        value = default
    if min_value is not None:
        value = max(min_value, value)
    if max_value is not None:
        value = min(max_value, value)
    return value


class Settings:
    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = resolve_groq_model()
        self.port = int(os.getenv("PORT", "8000"))
        self.jwt_secret = os.getenv("JWT_SECRET", "careerpilot-dev-secret-change-me").strip()
        self.jwt_expire_days = int(os.getenv("JWT_EXPIRE_DAYS", "7"))
        self.cookie_secure = os.getenv("COOKIE_SECURE", "").lower() in {"1", "true", "yes"}
        self.job_provider = os.getenv("JOB_PROVIDER", "auto").strip()
        self.adzuna_app_id = os.getenv("ADZUNA_APP_ID", "").strip()
        self.adzuna_app_key = os.getenv("ADZUNA_APP_KEY", "").strip()
        self.apify_token = (os.getenv("APIFY_API_TOKEN") or os.getenv("APIFY_TOKEN") or "").strip()
        self.apify_actor = (
            os.getenv("APIFY_JOBS_ACTOR_ID") or os.getenv("APIFY_ACTOR") or "khadinakbar/jobs-scraper"
        ).strip()
        self.apify_linkedin_actor_id = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "").strip()
        self.apify_actors = _csv(os.getenv("APIFY_ACTORS", ""))
        self.apify_platforms = [
            item
            for item in _csv(
                os.getenv("APIFY_PLATFORMS", "indeed,linkedin"),
                default=["indeed", "linkedin"],
            )
            if item.lower() != "glassdoor"
        ] or ["indeed", "linkedin"]
        self.apify_timeout_seconds = _int("APIFY_TIMEOUT_SECONDS", 180, min_value=30, max_value=300)
        self.apify_request_timeout_seconds = _int("APIFY_REQUEST_TIMEOUT_SECONDS", 30, min_value=5, max_value=90)
        self.apify_poll_interval_seconds = _int("APIFY_POLL_INTERVAL_SECONDS", 3, min_value=1, max_value=15)
        self.apify_retry_count = _int("APIFY_RETRY_COUNT", 0, min_value=0, max_value=2)
        self.apify_max_items = _int("APIFY_MAX_ITEMS", 50, min_value=1, max_value=100)
        self.search_limit = int(os.getenv("SEARCH_LIMIT", "20"))
        self.mysql_host = os.getenv("MYSQL_HOST", "127.0.0.1").strip()
        self.mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        self.mysql_user = os.getenv("MYSQL_USER", "careerpilot").strip()
        self.mysql_password = os.getenv("MYSQL_PASSWORD", "").strip()
        self.mysql_database = os.getenv("MYSQL_DATABASE", "careerpilot").strip()
        self.database_url = os.getenv("DATABASE_URL", "").strip() or (
            f"mysql+pymysql://{quote_plus(self.mysql_user)}:{quote_plus(self.mysql_password)}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def apify_actor_ids(self) -> list[str]:
        if self.apify_actors:
            return self.apify_actors
        actors = [self.apify_actor]
        if self.apify_linkedin_actor_id and self.apify_linkedin_actor_id not in actors:
            actors.append(self.apify_linkedin_actor_id)
        return actors


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
