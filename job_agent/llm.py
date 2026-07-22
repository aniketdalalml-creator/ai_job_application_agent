from __future__ import annotations

import json
import re
from typing import Any

from groq import Groq

from job_agent.config import Settings, get_groq_client, get_settings


def chat(
    messages: list[dict[str, str]],
    *,
    temperature: float | None = None,
    json_mode: bool = False,
    client: Groq | None = None,
    settings: Settings | None = None,
) -> str:
    """Call Groq chat completions and return the assistant text."""
    settings = settings or get_settings()
    client = client or get_groq_client()
    kwargs: dict[str, Any] = {
        "model": settings.groq_model,
        "messages": messages,
        "temperature": settings.temperature if temperature is None else temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    content = response.choices[0].message.content
    return (content or "").strip()


def extract_json(text: str) -> dict[str, Any]:
    """Parse JSON from a model response, tolerating markdown fences."""
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
