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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
