from __future__ import annotations

import re
from typing import Protocol

from backend.app.ai.models import CandidateProfile, NormalizedJob

MUSE_CATEGORIES = (
    "Software Engineering",
    "Data Science",
    "Design and UX",
    "Product",
    "Project Management",
    "Marketing",
    "Sales",
    "Finance",
    "Data and Analytics",
    "DevOps and Infrastructure",
)


class JobProvider(Protocol):
    def search(self, profile: CandidateProfile, *, limit: int = 20) -> list[NormalizedJob]:
        ...


def query_parts(profile: CandidateProfile) -> list[str]:
    parts = [item for item in profile.target_titles[:2] if item.strip()]
    parts.extend(item for item in profile.skills[:3] if item.strip())
    return parts


def search_text(profile: CandidateProfile) -> str:
    return " ".join(query_parts(profile)) or "software engineer"


def plain(value: str) -> str:
    text = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", text).strip()


def muse_category(profile: CandidateProfile) -> str:
    blob = " ".join([*profile.target_titles, *profile.skills]).lower()
    if any(token in blob for token in ("data", "machine learning", "ml ", "ai ", "analyst", "statistic")):
        return "Data Science"
    if any(token in blob for token in ("design", "ux", "ui", "figma")):
        return "Design and UX"
    if any(token in blob for token in ("product manager", "product management")):
        return "Product"
    return "Software Engineering"
