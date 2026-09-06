from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest

from backend.app.integrations.apify import ActorRun, ApifyClient, ApifyError, ApifyErrorCategory, actor_path


class FakeResponse:
    def __init__(self, payload, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300


class FakeClient:
    def __init__(self, response: FakeResponse | Exception) -> None:
        self.response = response

    def __enter__(self):
        return self

    def __exit__(self, *_exc) -> bool:
        return False

    def post(self, *_args, **_kwargs):
        return self._result()

    def get(self, *_args, **_kwargs):
        return self._result()

    def _result(self):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def test_actor_path_uses_tilde() -> None:
    assert actor_path("khadinakbar/jobs-scraper") == "khadinakbar~jobs-scraper"


def test_run_actor_returns_run() -> None:
    response = FakeResponse({"data": {"id": "run-1", "status": "RUNNING", "defaultDatasetId": ""}})

    with patch("backend.app.integrations.apify.client.httpx.Client", lambda **_k: FakeClient(response)):
        run = ApifyClient("token").run_actor("khadinakbar/jobs-scraper", {"searchQuery": "engineer"})

    assert run == ActorRun(id="run-1", status="RUNNING", default_dataset_id="")


def test_get_dataset_items() -> None:
    response = FakeResponse([{"job_title": "Engineer", "id": "1"}])

    with patch("backend.app.integrations.apify.client.httpx.Client", lambda **_k: FakeClient(response)):
        items = ApifyClient("token").get_dataset_items("ds-1", limit=10)

    assert items == [{"job_title": "Engineer", "id": "1"}]


def test_empty_dataset() -> None:
    with patch("backend.app.integrations.apify.client.httpx.Client", lambda **_k: FakeClient(FakeResponse([]))):
        assert ApifyClient("token").get_dataset_items("ds-1", limit=10) == []


def test_invalid_token() -> None:
    with patch(
        "backend.app.integrations.apify.client.httpx.Client",
        lambda **_k: FakeClient(FakeResponse({"error": {"message": "secret"}}, status_code=401)),
    ):
        with pytest.raises(ApifyError) as exc:
            ApifyClient("bad").run_actor("khadinakbar/jobs-scraper", {})
    assert exc.value.category is ApifyErrorCategory.INVALID_TOKEN
    assert "secret" not in str(exc.value)
    assert "token" not in str(exc.value).lower()


def test_actor_not_found() -> None:
    with patch(
        "backend.app.integrations.apify.client.httpx.Client",
        lambda **_k: FakeClient(FakeResponse({}, status_code=404)),
    ):
        with pytest.raises(ApifyError) as exc:
            ApifyClient("token").run_actor("missing/actor", {})
    assert exc.value.category is ApifyErrorCategory.ACTOR_NOT_FOUND


def test_rate_limit() -> None:
    with patch(
        "backend.app.integrations.apify.client.httpx.Client",
        lambda **_k: FakeClient(FakeResponse({}, status_code=429)),
    ):
        with pytest.raises(ApifyError) as exc:
            ApifyClient("token").run_actor("khadinakbar/jobs-scraper", {})
    assert exc.value.category is ApifyErrorCategory.RATE_LIMIT


def test_network_failure() -> None:
    with patch(
        "backend.app.integrations.apify.client.httpx.Client",
        lambda **_k: FakeClient(httpx.ConnectError("boom")),
    ):
        with pytest.raises(ApifyError) as exc:
            ApifyClient("token").run_actor("khadinakbar/jobs-scraper", {})
    assert exc.value.category is ApifyErrorCategory.NETWORK
    assert "boom" not in str(exc.value)


def test_invalid_response() -> None:
    with patch("backend.app.integrations.apify.client.httpx.Client", lambda **_k: FakeClient(FakeResponse(["nope"]))):
        with pytest.raises(ApifyError) as exc:
            ApifyClient("token").run_actor("khadinakbar/jobs-scraper", {})
    assert exc.value.category is ApifyErrorCategory.INVALID_RESPONSE


def test_wait_timeout() -> None:
    client = ApifyClient("token", poll_interval_seconds=1)
    running = ActorRun(id="run-1", status="RUNNING")

    with (
        patch.object(client, "get_run", return_value=running),
        patch("backend.app.integrations.apify.client.time.sleep", return_value=None),
        patch("backend.app.integrations.apify.client.time.monotonic", side_effect=[0, 1, 2, 200]),
    ):
        with pytest.raises(ApifyError) as exc:
            client.wait_for_run(running, timeout_seconds=30)
    assert exc.value.category is ApifyErrorCategory.TIMEOUT


def test_wait_run_failed() -> None:
    client = ApifyClient("token")
    with pytest.raises(ApifyError) as exc:
        client.wait_for_run(ActorRun(id="run-1", status="FAILED", default_dataset_id="ds"), timeout_seconds=30)
    assert exc.value.category is ApifyErrorCategory.RUN_FAILED


def test_wait_dataset_unavailable() -> None:
    client = ApifyClient("token")
    with pytest.raises(ApifyError) as exc:
        client.wait_for_run(ActorRun(id="run-1", status="SUCCEEDED"), timeout_seconds=30)
    assert exc.value.category is ApifyErrorCategory.DATASET_UNAVAILABLE


def test_config_error_without_token() -> None:
    with pytest.raises(ApifyError) as exc:
        ApifyClient("").run_actor("khadinakbar/jobs-scraper", {})
    assert exc.value.category is ApifyErrorCategory.CONFIG
