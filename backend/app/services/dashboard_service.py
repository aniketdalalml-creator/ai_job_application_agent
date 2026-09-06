from __future__ import annotations

from collections import defaultdict

from sqlmodel import Session, select

from backend.app.models import Application, FitAnalysisRow, Job, SearchRun


def build_insights(session: Session, user_id: str) -> dict:
    jobs = session.exec(select(Job).where(Job.user_id == user_id)).all()
    fits = session.exec(select(FitAnalysisRow).where(FitAnalysisRow.user_id == user_id)).all()
    applications = session.exec(select(Application).where(Application.user_id == user_id)).all()
    searches = session.exec(select(SearchRun).where(SearchRun.user_id == user_id)).all()

    latest_fit: dict[str, FitAnalysisRow] = {}
    for row in sorted(fits, key=lambda item: item.created_at):
        latest_fit[row.job_id] = row

    by_recommendation = {"APPLY": 0, "MAYBE": 0, "SKIP": 0}
    for row in latest_fit.values():
        key = row.recommendation if row.recommendation in by_recommendation else "MAYBE"
        by_recommendation[key] += 1

    scores = [row.overall_score for row in latest_fit.values()]
    avg_fit = round(sum(scores) / len(scores), 1) if scores else 0.0

    by_status: dict[str, int] = defaultdict(int)
    for application in applications:
        by_status[application.status] += 1

    title_scores: dict[str, list[float]] = defaultdict(list)
    for job in jobs:
        fit = latest_fit.get(job.id)
        if not fit:
            continue
        title = (job.title or "Untitled").strip()
        title_scores[title].append(fit.overall_score)
    avg_fit_by_title = [
        {"title": title, "avg_fit": round(sum(values) / len(values), 1), "count": len(values)}
        for title, values in title_scores.items()
    ]
    avg_fit_by_title.sort(key=lambda item: item["avg_fit"], reverse=True)

    conversion: dict[str, dict[str, int]] = {
        "APPLY": {"jobs": 0, "applied": 0},
        "MAYBE": {"jobs": 0, "applied": 0},
        "SKIP": {"jobs": 0, "applied": 0},
    }
    applied_job_ids = {
        item.job_id
        for item in applications
        if item.status in {"applied", "interviewing", "offer", "ready"}
    }
    for job in jobs:
        fit = latest_fit.get(job.id)
        if not fit:
            continue
        bucket = conversion.get(fit.recommendation, conversion["MAYBE"])
        bucket["jobs"] += 1
        if job.id in applied_job_ids:
            bucket["applied"] += 1

    conversion_by_tier = [
        {
            "recommendation": key,
            "jobs": value["jobs"],
            "moved_forward": value["applied"],
            "rate": round(100.0 * value["applied"] / value["jobs"], 1) if value["jobs"] else 0.0,
        }
        for key, value in conversion.items()
    ]

    suggestions: list[str] = []
    completed = [item for item in searches if item.status == "completed"]
    if avg_fit_by_title:
        top = avg_fit_by_title[0]
        suggestions.append(f"Highest-fit title so far: {top['title']} ({top['avg_fit']:.0f} avg).")
    if by_recommendation["SKIP"] > by_recommendation["APPLY"] and by_recommendation["SKIP"] > 3:
        suggestions.append("Many SKIP results — tighten target titles or location on your profile.")
    if completed:
        best = max(completed, key=lambda item: item.avg_fit)
        if best.query:
            suggestions.append(f"Best search query: “{best.query}” (avg fit {best.avg_fit:.0f}).")
    if not suggestions:
        suggestions.append("Save a profile and run a search to generate strategy insights.")

    return {
        "jobs_found": len(jobs),
        "avg_fit": avg_fit,
        "by_recommendation": by_recommendation,
        "applications_by_status": dict(by_status),
        "avg_fit_by_title": avg_fit_by_title[:8],
        "conversion_by_tier": conversion_by_tier,
        "suggestions": suggestions,
        "search_count": len(searches),
        "application_count": len(applications),
    }
