from __future__ import annotations

from enum import Enum


class ApifyErrorCategory(str, Enum):
    CONFIG = "config"
    INVALID_TOKEN = "invalid_token"
    ACTOR_NOT_FOUND = "actor_not_found"
    RUN_FAILED = "run_failed"
    DATASET_UNAVAILABLE = "dataset_unavailable"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"


SAFE_MESSAGES = {
    ApifyErrorCategory.CONFIG: "Job search is not configured.",
    ApifyErrorCategory.INVALID_TOKEN: "Job search is not authorized.",
    ApifyErrorCategory.ACTOR_NOT_FOUND: "Job search source is unavailable.",
    ApifyErrorCategory.RUN_FAILED: "Job search failed.",
    ApifyErrorCategory.DATASET_UNAVAILABLE: "Job search results are unavailable.",
    ApifyErrorCategory.TIMEOUT: "Job search timed out.",
    ApifyErrorCategory.INVALID_RESPONSE: "Job search returned an invalid result.",
    ApifyErrorCategory.NETWORK: "Job search is temporarily unavailable.",
    ApifyErrorCategory.RATE_LIMIT: "Job search is rate limited. Try again shortly.",
}


class ApifyError(Exception):
    """Controlled Apify failure. ``str(error)`` is safe for API/SSE clients."""

    def __init__(
        self,
        category: ApifyErrorCategory,
        *,
        actor: str = "",
        run_id: str = "",
        status_code: int | None = None,
    ) -> None:
        self.category = category
        self.actor = actor
        self.run_id = run_id
        self.status_code = status_code
        super().__init__(SAFE_MESSAGES[category])

    @property
    def user_message(self) -> str:
        return SAFE_MESSAGES[self.category]


def category_for_status(status_code: int, *, path: str = "") -> ApifyErrorCategory:
    if status_code in {401, 403}:
        return ApifyErrorCategory.INVALID_TOKEN
    if status_code == 404:
        if "dataset" in path:
            return ApifyErrorCategory.DATASET_UNAVAILABLE
        return ApifyErrorCategory.ACTOR_NOT_FOUND
    if status_code == 429:
        return ApifyErrorCategory.RATE_LIMIT
    if status_code >= 500:
        return ApifyErrorCategory.NETWORK
    return ApifyErrorCategory.INVALID_RESPONSE
