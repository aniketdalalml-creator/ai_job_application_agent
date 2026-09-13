from __future__ import annotations

import hashlib
from typing import Any

from backend.app.ai.models import NormalizedJob
from backend.app.integrations.jobs.apify.adapters import actor_key
from backend.app.integrations.jobs.base import plain


def _first(item: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = item.get(key)
        if value is None:
            continue
        if isinstance(value, dict):
            nested = _first(value, "name", "display_name", "title", "url")
            if nested:
                return nested
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def map_apify_record(item: Any, *, actor: str) -> NormalizedJob | None:
    """Map a raw Apify dataset record onto the canonical NormalizedJob."""
    if not isinstance(item, dict):
        return None
    title = _first(item, "job_title", "title", "jobTitle", "name", "position")
    url = _first(
        item,
        "apply_url",
        "applyUrl",
        "jobUrl",
        "job_url",
        "url",
        "link",
        "source_url",
    )
    company = _first(item, "company_name", "company", "companyName", "employer")
    location = _first(item, "location", "jobLocation", "formattedLocation")
    if item.get("is_remote") or item.get("isRemote"):
        location = location or "Remote"
    description = plain(
        _first(item, "description", "jobDescription", "descriptionText", "text", "snippet")
    )
    external_id = _first(item, "id", "job_id", "jobId", "jobKey", "external_id", "guid")
    if not external_id:
        fingerprint = url or f"{title}|{company}|{location}"
        if not fingerprint.strip("|"):
            return None
        external_id = hashlib.sha1(fingerprint.encode("utf-8")).hexdigest()[:16]
    if not title and not url:
        return None
    platform = _first(item, "platform", "source") or actor_key(actor).rsplit("/", 1)[-1]
    if "glassdoor" in platform.lower() or "glassdoor." in url.lower():
        return None
    return NormalizedJob(
        source="apify",
        external_id=f"{platform}:{external_id}",
        title=title,
        company=company,
        location=location or "Location n/a",
        description=description,
        url=url,
        raw=item,
    )


# Backward-compatible name used by earlier tests.
normalize_item = map_apify_record
