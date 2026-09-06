from __future__ import annotations

import httpx

from backend.app.ai.models import CandidateProfile, NormalizedJob
from backend.app.integrations.jobs.base import muse_category, plain


class MuseProvider:
    """https://www.themuse.com/developers/api/v2 — public, no API key required."""

    def search(self, profile: CandidateProfile, *, limit: int = 20) -> list[NormalizedJob]:
        params: list[tuple[str, str]] = [
            ("page", "0"),
            ("descending", "true"),
            ("category", muse_category(profile)),
        ]
        if profile.work_mode == "remote":
            params.append(("location", "Flexible / Remote"))
        elif profile.locations:
            params.append(("location", profile.locations[0]))

        results = self._fetch(params)
        if not results and profile.locations:
            results = self._fetch([("page", "0"), ("descending", "true"), ("category", muse_category(profile))])

        jobs: list[NormalizedJob] = []
        for item in results:
            external_id = str(item.get("id") or "")
            if not external_id:
                continue
            locations = item.get("locations") or []
            location = locations[0].get("name") if locations and isinstance(locations[0], dict) else ""
            refs = item.get("refs") or {}
            jobs.append(
                NormalizedJob(
                    source="muse",
                    external_id=external_id,
                    title=item.get("name") or "",
                    company=(item.get("company") or {}).get("name") or "",
                    location=location or "Location n/a",
                    description=plain(item.get("contents") or ""),
                    url=refs.get("landing_page") or "",
                    raw=item,
                )
            )
        return jobs[:limit]

    def _fetch(self, params: list[tuple[str, str]]) -> list[dict]:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            response = client.get("https://www.themuse.com/api/public/jobs", params=params)
            response.raise_for_status()
            payload = response.json()
        return list(payload.get("results") or [])
