from __future__ import annotations

import httpx

from backend.app.ai.models import CandidateProfile, NormalizedJob
from backend.app.integrations.jobs.base import query_parts


class AdzunaProvider:
    """https://developer.adzuna.com/"""

    def __init__(self, app_id: str, app_key: str) -> None:
        self.app_id = app_id.strip()
        self.app_key = app_key.strip()

    def search(self, profile: CandidateProfile, *, limit: int = 20) -> list[NormalizedJob]:
        if not self.app_id or not self.app_key:
            raise RuntimeError(
                "ADZUNA_APP_ID and ADZUNA_APP_KEY are required. "
                "Get free keys at https://developer.adzuna.com/"
            )

        country = (profile.country or "us").strip().lower()[:2]
        what = ", ".join(query_parts(profile)) or "software engineer"
        where = profile.locations[0] if profile.locations else ""
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(max(limit, 1), 50),
            "what": what,
            "content-type": "application/json",
        }
        if where:
            params["where"] = where
        if profile.work_mode == "remote":
            params["what"] = f"{what} remote"

        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        jobs: list[NormalizedJob] = []
        for item in payload.get("results") or []:
            company = (item.get("company") or {}).get("display_name") or ""
            location = (item.get("location") or {}).get("display_name") or ""
            external_id = str(item.get("id") or item.get("adref") or "")
            if not external_id:
                continue
            jobs.append(
                NormalizedJob(
                    source="adzuna",
                    external_id=external_id,
                    title=item.get("title") or "",
                    company=company,
                    location=location,
                    description=item.get("description") or "",
                    url=item.get("redirect_url") or item.get("url") or "",
                    raw=item,
                )
            )
        return jobs[:limit]
