from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

ProgressFn = Callable[..., None]

from backend.app.ai.models import CandidateProfile, NormalizedJob
from backend.app.core.config import Settings, get_settings
from backend.app.integrations.apify import ActorRun, ApifyClient, ApifyClientProtocol, ApifyError, ApifyErrorCategory
from backend.app.integrations.jobs.apify.adapters import DEFAULT_ACTOR, DEFAULT_PLATFORMS, build_actor_input
from backend.app.integrations.jobs.apify.mapper import map_apify_record

logger = logging.getLogger("careerpilot.apify")


class ApifyProvider:
    """Job-board provider. Talks to Apify only through ApifyClient."""

    def __init__(
        self,
        token: str = "",
        *,
        client: ApifyClientProtocol | None = None,
        actors: list[str] | None = None,
        platforms: list[str] | None = None,
        timeout_seconds: int = 180,
        max_items: int = 50,
    ) -> None:
        self.token = token.strip()
        self.actors = [item.strip() for item in (actors or [DEFAULT_ACTOR]) if item.strip()] or [DEFAULT_ACTOR]
        self.platforms = [item.strip().lower() for item in (platforms or list(DEFAULT_PLATFORMS)) if item.strip()]
        self.timeout_seconds = max(timeout_seconds, 30)
        self.max_items = min(max(max_items, 1), 100)
        self._client = client or ApifyClient(self.token)

    @classmethod
    def from_settings(cls, settings: Settings | None = None) -> ApifyProvider:
        cfg = settings or get_settings()
        client = ApifyClient(
            cfg.apify_token,
            request_timeout_seconds=cfg.apify_request_timeout_seconds,
            retry_count=cfg.apify_retry_count,
            poll_interval_seconds=cfg.apify_poll_interval_seconds,
        )
        return cls(
            cfg.apify_token,
            client=client,
            actors=cfg.apify_actor_ids,
            platforms=cfg.apify_platforms,
            timeout_seconds=cfg.apify_timeout_seconds,
            max_items=cfg.apify_max_items,
        )

    def search(
        self,
        profile: CandidateProfile,
        *,
        limit: int = 20,
        on_progress: ProgressFn | None = None,
    ) -> list[NormalizedJob]:
        if not self.token and not getattr(self._client, "token", ""):
            raise ApifyError(ApifyErrorCategory.CONFIG)

        collected: list[NormalizedJob] = []
        last_error: ApifyError | None = None
        for actor in self.actors:
            try:
                collected.extend(self._search_actor(actor, profile, limit=limit, on_progress=on_progress))
            except ApifyError as exc:
                last_error = exc
                logger.warning(
                    "apify.actor_failed category=%s actor=%s run_id=%s",
                    exc.category.value,
                    actor,
                    exc.run_id or "-",
                )

        unique = _unique(collected)
        if unique:
            return unique[:limit]
        if last_error:
            raise last_error
        raise ApifyError(ApifyErrorCategory.INVALID_RESPONSE)

    def _search_actor(
        self,
        actor: str,
        profile: CandidateProfile,
        *,
        limit: int,
        on_progress: ProgressFn | None = None,
    ) -> list[NormalizedJob]:
        payload = build_actor_input(
            actor,
            profile,
            limit=limit,
            platforms=self.platforms,
            max_items=self.max_items,
        )
        started = time.monotonic()
        logger.info("apify.run_started actor=%s", actor)
        _report(on_progress, "apify_start", "Starting Apify job scraper", percent=8, actor=actor)
        run = self._client.run_actor(actor, payload)
        _report(
            on_progress,
            "apify_running",
            "Apify scraper is running",
            percent=18,
            actor=actor,
            run_id=run.id,
        )
        run = self._wait(run, actor, on_progress=on_progress)
        _report(on_progress, "apify_collect", "Downloading Apify listings", percent=52, actor=actor, run_id=run.id)
        items = self._client.get_dataset_items(run.default_dataset_id, limit=min(max(limit, 1), self.max_items))
        jobs = self._map_items(items, actor=actor)
        _report(
            on_progress,
            "apify_done",
            f"Apify returned {len(jobs)} listing(s)",
            percent=58,
            actor=actor,
            run_id=run.id,
            count=len(jobs),
        )
        logger.info(
            "apify.run_finished actor=%s run_id=%s duration_ms=%s records=%s status=success",
            actor,
            run.id,
            int((time.monotonic() - started) * 1000),
            len(jobs),
        )
        return jobs

    def _wait(self, run: ActorRun, actor: str, on_progress: ProgressFn | None = None) -> ActorRun:
        def on_poll(*, elapsed: float, timeout: float, status: str) -> None:
            fraction = min(elapsed / timeout, 0.98)
            percent = 18 + int(32 * fraction)
            _report(
                on_progress,
                "apify_progress",
                f"Waiting on Apify ({int(elapsed)}s)",
                percent=percent,
                actor=actor,
                run_id=run.id,
                status=status,
            )

        try:
            return self._client.wait_for_run(run, timeout_seconds=self.timeout_seconds, on_poll=on_poll)
        except ApifyError as exc:
            logger.warning(
                "apify.run_finished actor=%s run_id=%s status=failure category=%s",
                actor,
                exc.run_id or run.id or "-",
                exc.category.value,
            )
            raise ApifyError(exc.category, actor=actor, run_id=exc.run_id or run.id) from exc

    def _map_items(self, items: list[dict[str, Any]], *, actor: str) -> list[NormalizedJob]:
        jobs: list[NormalizedJob] = []
        skipped = 0
        for item in items:
            job = map_apify_record(item, actor=actor)
            if job:
                jobs.append(job)
            else:
                skipped += 1
        if items and not jobs:
            logger.warning("apify.mapping_failed actor=%s skipped=%s", actor, skipped)
            raise ApifyError(ApifyErrorCategory.INVALID_RESPONSE, actor=actor)
        if skipped:
            logger.info("apify.mapping_skipped actor=%s skipped=%s mapped=%s", actor, skipped, len(jobs))
        return jobs


def _report(on_progress: ProgressFn | None, event_type: str, message: str, **payload: Any) -> None:
    if not on_progress:
        return
    on_progress(event_type, message, **payload)


def _unique(jobs: list[NormalizedJob]) -> list[NormalizedJob]:
    seen: set[tuple[str, str]] = set()
    unique: list[NormalizedJob] = []
    for job in jobs:
        key = (job.source, job.external_id)
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)
    return unique
