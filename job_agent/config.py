from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Load .env from project root (parent of the job_agent package), then CWD.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")
load_dotenv()


class Settings:
    """Runtime configuration loaded from environment variables."""

    def __init__(self) -> None:
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.max_search_results = int(os.getenv("MAX_SEARCH_RESULTS", "8"))
        self.temperature = float(os.getenv("GROQ_TEMPERATURE", "0.4"))

    def require_api_key(self) -> None:
        if not self.groq_api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your key "
                "from https://console.groq.com/"
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


@lru_cache(maxsize=1)
def get_groq_client() -> Groq:
    settings = get_settings()
    settings.require_api_key()
    return Groq(api_key=settings.groq_api_key)
