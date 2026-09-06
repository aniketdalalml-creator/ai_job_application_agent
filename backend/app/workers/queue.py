from __future__ import annotations

import threading
from datetime import datetime
from queue import Queue
from typing import Any, Literal

from sqlmodel import Session, select

from backend.app.core.config import get_settings
from backend.app.db.session import engine
from backend.app.models import Application, FitAnalysisRow, Job, Profile, SearchRun, User
from backend.app.integrations.jobs import get_provider
from backend.app.ai.fit_analyzer import analyze_fit
from backend.app.ai.models import CandidateProfile, FitAnalysis
from backend.app.ai.pipeline import run_pipeline

TaskKind = Literal["search", "fit", "prepare"]

_queue: Queue[tuple[TaskKind, str]] = Queue()
_started = False


def enqueue(kind: TaskKind, entity_id: str) -> None:
    _queue.put((kind, entity_id))


def start_worker() -> None:
    global _started
    if _started:
        return
    _started = True
    thread = threading.Thread(target=_loop, daemon=True, name="careerpilot-worker")
    thread.start()


def _loop() -> None:
    while True:
        kind, entity_id = _queue.get()
        try:
            if kind == "search":
                _run_search(entity_id)
            elif kind == "fit":
                _run_fit(entity_id)
            else:
                _run_prepare(entity_id)
        except Exception as exc:  # noqa: BLE001
            _mark_failed(kind, entity_id, str(exc))
        finally:
            _queue.task_done()


def _mark_failed(kind: TaskKind, entity_id: str, message: str) -> None:
    with Session(engine) as session:
        if kind == "search":
            run = session.get(SearchRun, entity_id)
            if run:
                run.status = "failed"
                run.error = message
                run.finished_at = datetime.utcnow()
                _append_event(run, "error", message)
                session.add(run)
        elif kind == "prepare":
            application = session.get(Application, entity_id)
            if application:
                application.status = "failed"
                application.error = message
                application.updated_at = datetime.utcnow()
                _append_event(application, "error", message)
                session.add(application)
        session.commit()


def _append_event(row: SearchRun | Application, event_type: str, message: str, **payload: Any) -> None:
    events = list(row.events or [])
    events.append(
        {
            "type": event_type,
            "message": message,
            "payload": payload or None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    )
    row.events = events


def _profile_to_candidate(profile: Profile, name: str) -> CandidateProfile:
    work_mode = profile.work_mode if profile.work_mode in {"on-site", "remote", "hybrid"} else "hybrid"
    return CandidateProfile(
        name=name,
        resume_text=profile.resume_text or "",
        target_titles=list(profile.target_titles or []),
        skills=list(profile.skills or []),
        years_experience=profile.years_experience or 0.0,
        locations=list(profile.locations or []),
        work_mode=work_mode,
        country=profile.country or "us",
    )


def _latest_fit(session: Session, user_id: str, job_id: str) -> FitAnalysisRow | None:
    return session.exec(
        select(FitAnalysisRow)
        .where(FitAnalysisRow.user_id == user_id, FitAnalysisRow.job_id == job_id)
        .order_by(FitAnalysisRow.created_at.desc())
    ).first()


def _persist_fit(
    session: Session,
    *,
    user_id: str,
    job_id: str,
    analysis: FitAnalysis,
    search_run_id: str | None = None,
) -> FitAnalysisRow:
    row = FitAnalysisRow(
        user_id=user_id,
        job_id=job_id,
        search_run_id=search_run_id,
        overall_score=analysis.overall_score,
        recommendation=analysis.recommendation,
        skill_match_score=analysis.skill_match_score,
        experience_match_score=analysis.experience_match_score,
        role_match_score=analysis.role_match_score,
        education_match_score=analysis.education_match_score,
        location_match_score=analysis.location_match_score,
        matched_skills=analysis.matched_skills,
        missing_required_skills=analysis.missing_required_skills,
        missing_preferred_skills=analysis.missing_preferred_skills,
        strengths=analysis.strengths,
        gaps=analysis.gaps,
        experience_assessment=analysis.experience_assessment,
        reasoning=analysis.reasoning,
        critical_gaps=analysis.critical_gaps,
    )
    session.add(row)
    return row


def _fit_from_row(row: FitAnalysisRow) -> FitAnalysis:
    return FitAnalysis(
        overall_score=row.overall_score,
        recommendation=row.recommendation if row.recommendation in {"APPLY", "MAYBE", "SKIP"} else "MAYBE",
        skill_match_score=row.skill_match_score,
        experience_match_score=row.experience_match_score,
        role_match_score=row.role_match_score,
        education_match_score=row.education_match_score,
        location_match_score=row.location_match_score,
        matched_skills=list(row.matched_skills or []),
        missing_required_skills=list(row.missing_required_skills or []),
        missing_preferred_skills=list(row.missing_preferred_skills or []),
        strengths=list(row.strengths or []),
        gaps=list(row.gaps or []),
        experience_assessment=row.experience_assessment or "",
        reasoning=row.reasoning or "",
        critical_gaps=list(row.critical_gaps or []),
    )


def _score_job(
    session: Session,
    job: Job,
    candidate: CandidateProfile,
    search_run_id: str | None = None,
) -> FitAnalysis:
    analysis = analyze_fit(candidate, job.title, job.description, job.location)
    _persist_fit(
        session,
        user_id=job.user_id,
        job_id=job.id,
        analysis=analysis,
        search_run_id=search_run_id,
    )
    return analysis


def _load_candidate(session: Session, user_id: str) -> CandidateProfile:
    profile = session.exec(select(Profile).where(Profile.user_id == user_id)).first()
    if not profile:
        raise RuntimeError("Save a profile before scoring a job.")
    user = session.get(User, user_id)
    return _profile_to_candidate(profile, user.name if user else "")


def _ensure_fit(session: Session, job: Job) -> FitAnalysis:
    existing = _latest_fit(session, job.user_id, job.id)
    if existing:
        return _fit_from_row(existing)
    candidate = _load_candidate(session, job.user_id)
    return _score_job(session, job, candidate)


def _run_fit(job_id: str) -> None:
    with Session(engine) as session:
        job = session.get(Job, job_id)
        if not job:
            return
        if _latest_fit(session, job.user_id, job.id):
            return
        candidate = _load_candidate(session, job.user_id)
        _score_job(session, job, candidate)
        session.commit()


def _run_search(search_id: str) -> None:
    settings = get_settings()
    with Session(engine) as session:
        run = session.get(SearchRun, search_id)
        if not run:
            return
        profile = session.exec(select(Profile).where(Profile.user_id == run.user_id)).first()
        if not profile:
            raise RuntimeError("Save a profile before searching for jobs.")
        if not (profile.resume_text or "").strip() and not (profile.target_titles or []):
            raise RuntimeError("Add target titles or a resume on your profile before searching.")

        run.status = "running"
        run.started_at = datetime.utcnow()
        _append_event(run, "pipeline_start", f"Searching jobs for: {run.query}")
        session.add(run)
        session.commit()

        user = session.get(User, run.user_id)
        candidate = _profile_to_candidate(profile, user.name if user else "")
        provider = get_provider(settings.job_provider, settings=settings)

        def on_progress(event_type: str, message: str, **payload: Any) -> None:
            with Session(engine) as inner:
                current = inner.get(SearchRun, search_id)
                if not current:
                    return
                _append_event(current, event_type, message, **payload)
                inner.add(current)
                inner.commit()

        if hasattr(provider, "search") and provider.__class__.__name__ in {"AutoProvider", "ApifyProvider"}:
            jobs = provider.search(candidate, limit=settings.search_limit, on_progress=on_progress)
        else:
            jobs = provider.search(candidate, limit=settings.search_limit)
        session.refresh(run)
        _append_event(run, "tool_result", f"Found {len(jobs)} posting(s)", count=len(jobs))
        session.add(run)
        session.commit()

        scores: list[float] = []
        for index, posting in enumerate(jobs, start=1):
            existing = session.exec(
                select(Job).where(
                    Job.user_id == run.user_id,
                    Job.source == posting.source,
                    Job.external_id == posting.external_id,
                )
            ).first()
            if existing:
                job = existing
                job.title = posting.title
                job.company = posting.company
                job.location = posting.location
                job.description = posting.description
                job.url = posting.url
                job.raw = posting.raw
                job.search_run_id = run.id
            else:
                job = Job(
                    user_id=run.user_id,
                    search_run_id=run.id,
                    source=posting.source,
                    external_id=posting.external_id,
                    title=posting.title,
                    company=posting.company,
                    location=posting.location,
                    description=posting.description,
                    url=posting.url,
                    raw=posting.raw,
                )
            session.add(job)
            session.flush()

            _append_event(run, "fit_start", f"Scoring {posting.title} at {posting.company} ({index}/{len(jobs)})")
            session.add(run)
            session.commit()

            analysis = _score_job(session, job, candidate, search_run_id=run.id)
            scores.append(analysis.overall_score)
            _append_event(
                run,
                "fit_result",
                f"{analysis.recommendation} · {analysis.overall_score:.0f} — {posting.title}",
                jobId=job.id,
                score=analysis.overall_score,
                recommendation=analysis.recommendation,
            )
            session.add(run)
            session.commit()

        run.result_count = len(jobs)
        run.avg_fit = round(sum(scores) / len(scores), 1) if scores else 0.0
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        _append_event(run, "pipeline_complete", f"Ranked {len(jobs)} jobs. Average fit {run.avg_fit:.0f}.")
        session.add(run)
        session.commit()


def _run_prepare(application_id: str) -> None:
    with Session(engine) as session:
        application = session.get(Application, application_id)
        if not application:
            return
        job = session.get(Job, application.job_id)
        profile = session.exec(select(Profile).where(Profile.user_id == application.user_id)).first()
        if not job or not profile:
            raise RuntimeError("Job or profile missing.")
        resume = (profile.resume_text or "").strip()
        if not resume:
            raise RuntimeError("Add your resume on the Profile page before generating materials.")

        application.status = "generating"
        application.error = ""
        application.updated_at = datetime.utcnow()
        _append_event(application, "pipeline_start", f"Preparing application for {job.company}")
        session.add(application)
        session.commit()

        fit = _ensure_fit(session, job)
        session.commit()

        def on_event(event_type: str, message: str) -> None:
            with Session(engine) as inner:
                row = inner.get(Application, application_id)
                if not row:
                    return
                _append_event(row, event_type, message)
                inner.add(row)
                inner.commit()

        on_event("agent_start", f"Researching {job.company}")
        result = run_pipeline(
            company_name=job.company or job.title,
            job_description=job.description,
            resume_text=resume,
            verbose=False,
            fit=fit,
        )
        on_event("handoff", "Research handoff ready")
        on_event("draft", "Draft materials written")
        on_event("critique", "Critique complete")
        if result.revised:
            on_event("revise", "Materials revised")
        on_event("pipeline_complete", "Application package ready")

    with Session(engine) as session:
        application = session.get(Application, application_id)
        if not application:
            return
        application.cover_letter = result.final_materials.coverLetter
        application.resume_bullets = result.final_materials.resumeBullets
        application.research = result.research.model_dump()
        application.critique = result.critique.model_dump()
        application.revised = result.revised
        application.status = "ready"
        application.updated_at = datetime.utcnow()
        session.add(application)
        session.commit()
