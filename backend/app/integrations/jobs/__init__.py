from __future__ import annotations

from backend.app.ai.models import CandidateProfile, NormalizedJob
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.jobs.adzuna import AdzunaProvider
from backend.app.integrations.jobs.apify import ApifyProvider
from backend.app.integrations.jobs.base import JobProvider
from backend.app.integrations.jobs.remotive import RemotiveProvider
from backend.app.integrations.jobs.themuse import MuseProvider


class PublicBoardsProvider:
    """Merge Remotive + The Muse when Adzuna keys are not available."""

    def search(self, profile: CandidateProfile, *, limit: int = 20) -> list[NormalizedJob]:
        buckets: list[list[NormalizedJob]] = []
        errors: list[str] = []
        for provider in (RemotiveProvider(), MuseProvider()):
            try:
                buckets.append(provider.search(profile, limit=limit))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider.__class__.__name__}: {exc}")

        collected: list[NormalizedJob] = []
        for index in range(max((len(bucket) for bucket in buckets), default=0)):
            for bucket in buckets:
                if index < len(bucket):
                    collected.append(bucket[index])

        if not collected:
            detail = "; ".join(errors) if errors else "no results"
            raise RuntimeError(f"Public job boards returned no postings ({detail}).")

        seen: set[tuple[str, str]] = set()
        unique: list[NormalizedJob] = []
        for job in collected:
            key = (job.source, job.external_id)
            if key in seen:
                continue
            seen.add(key)
            unique.append(job)
        return unique[:limit]


class AutoProvider:
    """Apify when token exists, else Adzuna, else Remotive + The Muse."""

    def __init__(
        self,
        adzuna_app_id: str = "",
        adzuna_app_key: str = "",
        *,
        apify: ApifyProvider | None = None,
    ) -> None:
        self.adzuna_app_id = adzuna_app_id.strip()
        self.adzuna_app_key = adzuna_app_key.strip()
        self.apify = apify

    def search(self, profile: CandidateProfile, *, limit: int = 20, on_progress=None) -> list[NormalizedJob]:
        if self.apify and self.apify.token:
            try:
                jobs = self.apify.search(profile, limit=limit, on_progress=on_progress)
                if jobs:
                    return jobs
            except Exception:  # noqa: BLE001
                if on_progress:
                    on_progress(
                        "apify_fallback",
                        "Apify unavailable, using public job boards",
                        percent=22,
                    )
        if self.adzuna_app_id and self.adzuna_app_key:
            try:
                jobs = AdzunaProvider(self.adzuna_app_id, self.adzuna_app_key).search(profile, limit=limit)
                if jobs:
                    return jobs
            except Exception:  # noqa: BLE001
                pass
        return PublicBoardsProvider().search(profile, limit=limit)


def apify_from_settings(settings: Settings | None = None) -> ApifyProvider:
    return ApifyProvider.from_settings(settings or get_settings())


def get_provider(
    name: str = "auto",
    *,
    adzuna_app_id: str = "",
    adzuna_app_key: str = "",
    settings: Settings | None = None,
) -> JobProvider:
    cfg = settings or get_settings()
    provider = (name or cfg.job_provider or "auto").strip().lower()
    if provider == "remotive":
        return RemotiveProvider()
    if provider in {"muse", "themuse"}:
        return MuseProvider()
    if provider == "apify":
        return apify_from_settings(cfg)
    if provider in {"adzuna", "auto", "public", ""}:
        return AutoProvider(
            adzuna_app_id or cfg.adzuna_app_id,
            adzuna_app_key or cfg.adzuna_app_key,
            apify=apify_from_settings(cfg),
        )
    raise RuntimeError(f"Unsupported JOB_PROVIDER: {provider}")


__all__ = [
    "AdzunaProvider",
    "ApifyProvider",
    "AutoProvider",
    "JobProvider",
    "MuseProvider",
    "PublicBoardsProvider",
    "RemotiveProvider",
    "get_provider",
]
