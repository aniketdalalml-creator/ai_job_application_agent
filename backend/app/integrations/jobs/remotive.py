from __future__ import annotations

import httpx

from backend.app.ai.models import CandidateProfile, NormalizedJob
from backend.app.integrations.jobs.base import plain, search_text


class RemotiveProvider:
    """https://remotive.com/api/remote-jobs — public, no API key."""

    def search(self, profile: CandidateProfile, *, limit: int = 20) -> list[NormalizedJob]:
        params = {"search": search_text(profile), "limit": min(max(limit, 1), 50)}
        with httpx.Client(timeout=30.0) as client:
            response = client.get("https://remotive.com/api/remote-jobs", params=params)
            response.raise_for_status()
            payload = response.json()

        jobs: list[NormalizedJob] = []
        for item in payload.get("jobs") or []:
            external_id = str(item.get("id") or "")
            if not external_id:
                continue
            jobs.append(
                NormalizedJob(
                    source="remotive",
                    external_id=external_id,
                    title=item.get("title") or "",
                    company=item.get("company_name") or "",
                    location=item.get("candidate_required_location") or "Remote",
                    description=plain(item.get("description") or ""),
                    url=item.get("url") or "",
                    raw=item,
                )
            )
        return jobs[:limit]
