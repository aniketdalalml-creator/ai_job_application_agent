from __future__ import annotations

import inspect

import pytest

from backend.app.ai.models import CandidateProfile, NormalizedJob
from backend.app.integrations.apify import ActorRun, ApifyError, ApifyErrorCategory
from backend.app.integrations.jobs.apify import ApifyProvider, build_actor_input, normalize_item
from backend.app.integrations.jobs.apify.mapper import map_apify_record


class FakeApifyClient:
    def __init__(
        self,
        *,
        run: ActorRun | None = None,
        items: list[dict] | None = None,
        error: Exception | None = None,
        token: str = "token",
    ) -> None:
        self.token = token
        self.run = run or ActorRun(id="run-1", status="SUCCEEDED", default_dataset_id="ds-1")
        self.items = items if items is not None else [
            {
                "job_title": "Platform Engineer",
                "company_name": "Initech",
                "location": "New York, NY",
                "apply_url": "https://indeed.com/viewjob?jk=xyz",
                "platform": "indeed",
                "id": "xyz",
            }
        ]
        self.error = error
        self.calls: list[tuple] = []

    def run_actor(self, actor_id: str, run_input: dict) -> ActorRun:
        self.calls.append(("run_actor", actor_id, run_input))
        if self.error:
            raise self.error
        return self.run

    def get_run(self, run_id: str) -> ActorRun:
        self.calls.append(("get_run", run_id))
        if self.error:
            raise self.error
        return self.run

    def get_dataset_items(self, dataset_id: str, *, limit: int) -> list[dict]:
        self.calls.append(("get_dataset_items", dataset_id, limit))
        if self.error:
            raise self.error
        return self.items[:limit]

    def wait_for_run(self, run: ActorRun, *, timeout_seconds: int, on_poll=None) -> ActorRun:
        self.calls.append(("wait_for_run", run.id, timeout_seconds))
        if self.error:
            raise self.error
        return self.run


def test_default_actor_input() -> None:
    profile = CandidateProfile(target_titles=["Data Engineer"], locations=["Austin, TX"], work_mode="hybrid")
    payload = build_actor_input("khadinakbar/jobs-scraper", profile, limit=12, platforms=["indeed", "linkedin"])
    assert payload["searchQuery"] == "Data Engineer"
    assert payload["location"] == "Austin, TX"
    assert payload["maxResults"] == 12
    assert payload["platforms"] == ["indeed", "linkedin"]
    assert payload["isRemote"] is False


def test_linkedin_actor_input() -> None:
    profile = CandidateProfile(target_titles=["ML Engineer"], work_mode="remote", country="us")
    payload = build_actor_input("curious_coder/linkedin-jobs-scraper", profile, limit=8, platforms=[])
    assert payload["keywords"] == "ML Engineer"
    assert payload["location"] == "Remote"
    assert payload["limitPerSource"] == 8


def test_normalize_khadinakbar_item() -> None:
    job = normalize_item(
        {
            "job_title": "Backend Engineer",
            "company_name": "Acme",
            "location": "Remote",
            "description": "<p>Python and FastAPI</p>",
            "apply_url": "https://www.linkedin.com/jobs/view/1",
            "platform": "linkedin",
            "id": "1",
        },
        actor="khadinakbar/jobs-scraper",
    )
    assert job is not None
    assert job.source == "apify"
    assert job.external_id == "linkedin:1"
    assert job.title == "Backend Engineer"
    assert job.company == "Acme"
    assert job.description == "Python and FastAPI"


def test_normalize_skips_glassdoor() -> None:
    job = map_apify_record(
        {
            "job_title": "Software Engineer II",
            "company_name": "Penske",
            "apply_url": "https://www.glassdoor.co.in/job-listing/software-engineer.htm",
            "platform": "glassdoor",
            "id": "123",
        },
        actor="khadinakbar/jobs-scraper",
    )
    assert job is None


def test_actor_input_drops_glassdoor() -> None:
    profile = CandidateProfile(target_titles=["Engineer"], locations=["India"])
    payload = build_actor_input(
        "khadinakbar/jobs-scraper",
        profile,
        limit=10,
        platforms=["indeed", "glassdoor", "linkedin"],
    )
    assert payload["platforms"] == ["indeed", "linkedin"]


def test_normalize_generic_item_hashes_url() -> None:
    job = map_apify_record(
        {"title": "Analyst", "company": "Globex", "url": "https://indeed.com/viewjob?jk=abc"},
        actor="custom/actor",
    )
    assert job is not None
    assert job.external_id.startswith("actor:")
    assert job.url == "https://indeed.com/viewjob?jk=abc"


def test_search_reports_progress() -> None:
    updates: list[tuple] = []
    client = FakeApifyClient()
    jobs = ApifyProvider("token", client=client).search(
        CandidateProfile(target_titles=["Platform Engineer"]),
        limit=5,
        on_progress=lambda event_type, message, **payload: updates.append((event_type, payload.get("percent"))),
    )
    assert jobs
    types = [item[0] for item in updates]
    assert "apify_start" in types
    assert "apify_done" in types
    assert updates[-1][1] == 58


def test_successful_actor_execution() -> None:
    client = FakeApifyClient()
    jobs = ApifyProvider("token", client=client).search(
        CandidateProfile(target_titles=["Platform Engineer"]),
        limit=5,
    )
    assert len(jobs) == 1
    assert isinstance(jobs[0], NormalizedJob)
    assert jobs[0].title == "Platform Engineer"
    assert jobs[0].company == "Initech"
    assert jobs[0].source == "apify"
    assert any(call[0] == "run_actor" for call in client.calls)
    assert any(call[0] == "get_dataset_items" for call in client.calls)


def test_empty_dataset() -> None:
    client = FakeApifyClient(items=[])
    with pytest.raises(ApifyError) as exc:
        ApifyProvider("token", client=client).search(CandidateProfile(target_titles=["Engineer"]))
    assert exc.value.category is ApifyErrorCategory.INVALID_RESPONSE


def test_actor_failure() -> None:
    client = FakeApifyClient(error=ApifyError(ApifyErrorCategory.RUN_FAILED, run_id="run-1"))
    with pytest.raises(ApifyError) as exc:
        ApifyProvider("token", client=client).search(CandidateProfile(target_titles=["Engineer"]))
    assert exc.value.category is ApifyErrorCategory.RUN_FAILED
    assert str(exc.value) == "Job search failed."


def test_timeout() -> None:
    client = FakeApifyClient(error=ApifyError(ApifyErrorCategory.TIMEOUT, run_id="run-1"))
    with pytest.raises(ApifyError) as exc:
        ApifyProvider("token", client=client).search(CandidateProfile(target_titles=["Engineer"]))
    assert exc.value.category is ApifyErrorCategory.TIMEOUT


def test_invalid_response() -> None:
    client = FakeApifyClient(error=ApifyError(ApifyErrorCategory.INVALID_RESPONSE))
    with pytest.raises(ApifyError) as exc:
        ApifyProvider("token", client=client).search(CandidateProfile(target_titles=["Engineer"]))
    assert exc.value.category is ApifyErrorCategory.INVALID_RESPONSE


def test_mapping_failure() -> None:
    client = FakeApifyClient(items=[{"unrelated": True}])
    with pytest.raises(ApifyError) as exc:
        ApifyProvider("token", client=client).search(CandidateProfile(target_titles=["Engineer"]))
    assert exc.value.category is ApifyErrorCategory.INVALID_RESPONSE


def test_configuration_error() -> None:
    with pytest.raises(ApifyError) as exc:
        ApifyProvider("").search(CandidateProfile())
    assert exc.value.category is ApifyErrorCategory.CONFIG
    assert "token" not in str(exc.value).lower()


def test_job_service_does_not_import_apify() -> None:
    import backend.app.services.job_service as job_service
    import backend.app.services.matching_service as matching_service

    assert "apify" not in inspect.getsource(job_service).lower()
    assert "apify" not in inspect.getsource(matching_service).lower()
    assert "ApifyClient" not in inspect.getsource(job_service)
    assert "ApifyClient" not in inspect.getsource(matching_service)
