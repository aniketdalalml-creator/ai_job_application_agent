from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from groq import Groq

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
load_dotenv(_PROJECT_ROOT / ".env", override=True)
load_dotenv()

DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
_RETIRED_GROQ_MODELS = {
    "llama-3.3-70b-versatile",
    "llama-3.1-70b-versatile",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
}


def resolve_groq_model(raw: str | None = None) -> str:
    model = (raw if raw is not None else os.getenv("GROQ_MODEL", "")).strip()
    if not model or model in _RETIRED_GROQ_MODELS:
        return DEFAULT_GROQ_MODEL
    return model


class Settings:
    """LLM runtime settings used by agents."""

    def __init__(self) -> None:
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        if not groq_key or "your_key" in groq_key:
            anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
            if anthropic_key.startswith("gsk_"):
                groq_key = anthropic_key

        self.groq_api_key = groq_key
        self.groq_model = resolve_groq_model()
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


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    json_mode: bool = False,
    client: Groq | None = None,
    settings: Settings | None = None,
) -> str:
    settings = settings or get_settings()
    client = client or get_groq_client()
    kwargs: dict[str, Any] = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": settings.temperature if temperature is None else temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as exc:
        if not json_mode or "json_validate_failed" not in str(exc):
            raise
        kwargs.pop("response_format", None)
        response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    return (content or "").strip()


def extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    if fence:
        cleaned = fence.group(1).strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        data = json.loads(cleaned[start : end + 1])
        if isinstance(data, dict):
            return data

    raise ValueError(f"Could not parse JSON from model response:\n{text[:500]}")
