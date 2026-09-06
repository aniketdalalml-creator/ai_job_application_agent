from __future__ import annotations

from backend.app.ai.profile_interview import interview_from_profile, profile_snapshot, run_interview_turn
from backend.app.repositories.profile_repository import ProfileRepository
from backend.app.schemas import InterviewState, ProfileChatIn, ProfileChatOut, ProfileOut
from backend.app.services.profile_service import apply_snapshot


def chat(repo: ProfileRepository, user_id: str, payload: ProfileChatIn) -> ProfileChatOut:
    profile = repo.ensure(user_id)
    if payload.profile is not None:
        incoming = payload.profile.model_dump()
        incoming["resume_text"] = incoming.get("resume_text") or profile.resume_text
        apply_snapshot(profile, incoming)

    snapshot = profile_snapshot(profile)
    interview_in = payload.interview.model_dump() if payload.interview else interview_from_profile(snapshot)
    message = payload.message.strip()
    if not message and payload.messages:
        last_user = next((item.content for item in reversed(payload.messages) if item.role == "user"), "")
        message = last_user.strip()

    updated, interview, assistant = run_interview_turn(
        profile=snapshot,
        action=payload.action,
        message=message,
        interview=interview_in,
    )
    apply_snapshot(profile, updated)
    repo.add(profile)
    repo.session.commit()
    repo.session.refresh(profile)
    return ProfileChatOut(
        profile=ProfileOut.model_validate(profile),
        interview=InterviewState.model_validate(interview),
        assistant_message=assistant,
    )
