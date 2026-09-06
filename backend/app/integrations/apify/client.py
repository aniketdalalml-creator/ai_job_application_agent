from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import quote

import httpx

from backend.app.integrations.apify.errors import ApifyError, ApifyErrorCategory, category_for_status

APIFY_API = "https://api.apify.com/v2"
TERMINAL_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}
logger = logging.getLogger("careerpilot.apify")


@dataclass(frozen=True)
class ActorRun:
    id: str
    status: str
    default_dataset_id: str = ""
    status_message: str = ""


class ApifyClientProtocol(Protocol):
    def run_actor(self, actor_id: str, run_input: dict[str, Any]) -> ActorRun: ...

    def get_run(self, run_id: str) -> ActorRun: ...

    def get_dataset_items(self, dataset_id: str, *, limit: int) -> list[dict[str, Any]]: ...

    def wait_for_run(self, run: ActorRun, *, timeout_seconds: int, on_poll: Any | None = None) -> ActorRun: ...


def actor_path(actor_id: str) -> str:
    cleaned = actor_id.strip().lstrip("/")
    if not cleaned:
        raise ApifyError(ApifyErrorCategory.CONFIG)
    return quote(cleaned.replace("/", "~"), safe="~")


class ApifyClient:
    """HTTP adapter for the official Apify REST API. No job-domain knowledge."""

    def __init__(
        self,
        token: str,
        *,
        request_timeout_seconds: int = 30,
        retry_count: int = 0,
        poll_interval_seconds: int = 3,
    ) -> None:
        self._token = token.strip()
        self.request_timeout_seconds = max(request_timeout_seconds, 5)
        self.retry_count = min(max(retry_count, 0), 2)
        self.poll_interval_seconds = min(max(poll_interval_seconds, 1), 15)

    @property
    def token(self) -> str:
        return self._token

    def run_actor(self, actor_id: str, run_input: dict[str, Any]) -> ActorRun:
        if not self._token:
            raise ApifyError(ApifyErrorCategory.CONFIG, actor=actor_id)
        url = f"{APIFY_API}/acts/{actor_path(actor_id)}/runs"
        timeout = max(self.request_timeout_seconds, 90)
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.post(
                    url,
                    headers=self._headers(),
                    json=run_input,
                    params={"waitForFinish": 60},
                )
        except httpx.TimeoutException as exc:
            raise ApifyError(ApifyErrorCategory.TIMEOUT, actor=actor_id) from exc
        except httpx.RequestError as exc:
            raise ApifyError(ApifyErrorCategory.NETWORK, actor=actor_id) from exc
        self._raise_http(response, actor=actor_id, path="acts")
        return self._parse_run(response.json(), actor=actor_id)

    def get_run(self, run_id: str) -> ActorRun:
        url = f"{APIFY_API}/actor-runs/{run_id}"
        response = self._get(url, path="actor-runs", run_id=run_id)
        return self._parse_run(response.json(), run_id=run_id)

    def get_dataset_items(self, dataset_id: str, *, limit: int) -> list[dict[str, Any]]:
        if not dataset_id:
            raise ApifyError(ApifyErrorCategory.DATASET_UNAVAILABLE)
        url = f"{APIFY_API}/datasets/{dataset_id}/items"
        response = self._get(
            url,
            path="datasets",
            params={"format": "json", "limit": min(max(limit, 1), 100)},
        )
        payload = response.json()
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return [item for item in payload["items"] if isinstance(item, dict)]
        raise ApifyError(ApifyErrorCategory.INVALID_RESPONSE)

    def wait_for_run(
        self,
        run: ActorRun,
        *,
        timeout_seconds: int,
        on_poll: Any | None = None,
    ) -> ActorRun:
        if run.status in TERMINAL_STATUSES:
            return self._finalize(run)
        if not run.id:
            raise ApifyError(ApifyErrorCategory.INVALID_RESPONSE)
        started = time.monotonic()
        timeout = max(timeout_seconds, 30)
        deadline = started + timeout
        while time.monotonic() < deadline:
            elapsed = time.monotonic() - started
            if on_poll:
                on_poll(elapsed=elapsed, timeout=timeout, status=run.status)
            time.sleep(self.poll_interval_seconds)
            run = self.get_run(run.id)
            if run.status in TERMINAL_STATUSES:
                return self._finalize(run)
        raise ApifyError(ApifyErrorCategory.TIMEOUT, run_id=run.id)

    def _finalize(self, run: ActorRun) -> ActorRun:
        if run.status != "SUCCEEDED":
            raise ApifyError(ApifyErrorCategory.RUN_FAILED, run_id=run.id)
        if not run.default_dataset_id:
            raise ApifyError(ApifyErrorCategory.DATASET_UNAVAILABLE, run_id=run.id)
        return run

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}

    def _get(
        self,
        url: str,
        *,
        path: str,
        params: dict[str, Any] | None = None,
        actor: str = "",
        run_id: str = "",
    ) -> httpx.Response:
        last_error: ApifyError | None = None
        attempts = 1 + self.retry_count
        for attempt in range(attempts):
            try:
                with httpx.Client(timeout=self.request_timeout_seconds, follow_redirects=True) as client:
                    response = client.get(url, headers=self._headers(), params=params)
                if response.status_code == 429 and attempt + 1 < attempts:
                    last_error = ApifyError(
                        ApifyErrorCategory.RATE_LIMIT, actor=actor, run_id=run_id, status_code=429
                    )
                    time.sleep(0.25)
                    continue
                self._raise_http(response, actor=actor, run_id=run_id, path=path)
                return response
            except httpx.TimeoutException as exc:
                last_error = ApifyError(ApifyErrorCategory.TIMEOUT, actor=actor, run_id=run_id)
                last_error.__cause__ = exc
            except httpx.RequestError as exc:
                last_error = ApifyError(ApifyErrorCategory.NETWORK, actor=actor, run_id=run_id)
                last_error.__cause__ = exc
            except ApifyError as exc:
                if exc.category in {ApifyErrorCategory.NETWORK, ApifyErrorCategory.RATE_LIMIT} and attempt + 1 < attempts:
                    last_error = exc
                    time.sleep(0.25)
                    continue
                raise
            if attempt + 1 < attempts:
                time.sleep(0.25)
        raise last_error or ApifyError(ApifyErrorCategory.NETWORK, actor=actor, run_id=run_id)

    def _raise_http(self, response: httpx.Response, *, actor: str = "", run_id: str = "", path: str = "") -> None:
        if response.is_success:
            return
        category = category_for_status(response.status_code, path=path)
        logger.warning(
            "apify.http_error category=%s status=%s actor=%s run_id=%s path=%s",
            category.value,
            response.status_code,
            actor or "-",
            run_id or "-",
            path or "-",
        )
        raise ApifyError(category, actor=actor, run_id=run_id, status_code=response.status_code)

    def _parse_run(self, payload: Any, *, actor: str = "", run_id: str = "") -> ActorRun:
        data = _unwrap(payload)
        parsed_id = str(data.get("id") or run_id or "")
        if not parsed_id:
            raise ApifyError(ApifyErrorCategory.INVALID_RESPONSE, actor=actor, run_id=run_id)
        return ActorRun(
            id=parsed_id,
            status=str(data.get("status") or ""),
            default_dataset_id=str(data.get("defaultDatasetId") or ""),
            status_message=str(data.get("statusMessage") or ""),
        )


def _unwrap(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
        return payload["data"]
    if isinstance(payload, dict):
        return payload
    raise ApifyError(ApifyErrorCategory.INVALID_RESPONSE)
