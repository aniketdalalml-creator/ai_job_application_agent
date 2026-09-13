from __future__ import annotations

from typing import Any, Protocol

from backend.app.ai.models import CandidateProfile
from backend.app.integrations.jobs.base import search_text

DEFAULT_ACTOR = "khadinakbar/jobs-scraper"
DEFAULT_PLATFORMS = ("indeed", "linkedin")
BLOCKED_PLATFORMS = frozenset({"glassdoor"})
COUNTRY_LABELS = {
    "us": "United States",
    "gb": "United Kingdom",
    "uk": "United Kingdom",
    "in": "India",
    "ca": "Canada",
    "au": "Australia",
    "de": "Germany",
    "fr": "France",
    "nl": "Netherlands",
    "ie": "Ireland",
    "sg": "Singapore",
}


def actor_key(actor_id: str) -> str:
    return actor_id.strip().lower().replace("~", "/")


def profile_location(profile: CandidateProfile) -> str:
    if profile.work_mode == "remote":
        return "Remote"
    if profile.locations:
        return profile.locations[0].strip()
    country = (profile.country or "us").strip().lower()
    return COUNTRY_LABELS.get(country, country.upper() or "United States")


def clamp_limit(limit: int, *, max_items: int = 50) -> int:
    return min(max(limit, 1), max(max_items, 1))


def sanitize_platforms(platforms: list[str]) -> list[str]:
    cleaned = [
        item.strip().lower()
        for item in platforms
        if item.strip() and item.strip().lower() not in BLOCKED_PLATFORMS
    ]
    return cleaned or list(DEFAULT_PLATFORMS)


class ActorAdapter(Protocol):
    def matches(self, actor_id: str) -> bool: ...

    def build_input(
        self,
        profile: CandidateProfile,
        *,
        limit: int,
        platforms: list[str],
        max_items: int,
    ) -> dict[str, Any]: ...


class JobsScraperAdapter:
    """Input contract for the existing multi-board jobs scraper."""

    def matches(self, actor_id: str) -> bool:
        key = actor_key(actor_id)
        if "linkedin-jobs" in key:
            return False
        return "khadinakbar" in key or key.endswith("/jobs-scraper")

    def build_input(
        self,
        profile: CandidateProfile,
        *,
        limit: int,
        platforms: list[str],
        max_items: int,
    ) -> dict[str, Any]:
        return {
            "searchQuery": search_text(profile),
            "location": profile_location(profile),
            "platforms": sanitize_platforms(platforms),
            "maxResults": clamp_limit(limit, max_items=max_items),
            "jobType": "all",
            "isRemote": profile.work_mode == "remote",
            "hoursOld": 0,
            "deduplicate": True,
        }


class LinkedInJobsAdapter:
    """Input contract for the existing LinkedIn jobs scraper."""

    def matches(self, actor_id: str) -> bool:
        key = actor_key(actor_id)
        return "curious_coder" in key and "linkedin-jobs" in key

    def build_input(
        self,
        profile: CandidateProfile,
        *,
        limit: int,
        platforms: list[str],
        max_items: int,
    ) -> dict[str, Any]:
        return {
            "keywords": search_text(profile),
            "location": profile_location(profile),
            "limitPerSource": clamp_limit(limit, max_items=max_items),
            "autoConvertToAiSearch": True,
            "datePosted": "anyTime",
        }


class GenericJobAdapter:
    def matches(self, actor_id: str) -> bool:
        return True

    def build_input(
        self,
        profile: CandidateProfile,
        *,
        limit: int,
        platforms: list[str],
        max_items: int,
    ) -> dict[str, Any]:
        query = search_text(profile)
        max_results = clamp_limit(limit, max_items=max_items)
        return {
            "searchQuery": query,
            "query": query,
            "keywords": query,
            "location": profile_location(profile),
            "maxResults": max_results,
            "maxItems": max_results,
            "isRemote": profile.work_mode == "remote",
        }


ADAPTERS: tuple[ActorAdapter, ...] = (
    LinkedInJobsAdapter(),
    JobsScraperAdapter(),
    GenericJobAdapter(),
)


def build_actor_input(
    actor_id: str,
    profile: CandidateProfile,
    *,
    limit: int,
    platforms: list[str],
    max_items: int = 50,
) -> dict[str, Any]:
    for adapter in ADAPTERS:
        if adapter.matches(actor_id):
            return adapter.build_input(
                profile, limit=limit, platforms=platforms, max_items=max_items
            )
    return GenericJobAdapter().build_input(
        profile, limit=limit, platforms=platforms, max_items=max_items
    )
