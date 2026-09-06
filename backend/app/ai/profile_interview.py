"""Ask about weak profile fields; infer when the user skips."""

from __future__ import annotations

from typing import Any

from backend.app.integrations.llm import chat, extract_json

PROFILE_FIELDS = (
    "target_titles",
    "skills",
    "years_experience",
    "locations",
    "work_mode",
    "country",
)

CONFIDENCE_THRESHOLD = 0.65

FIELD_QUESTIONS = {
    "target_titles": "Which job titles should we search for?",
    "skills": "Which skills matter most for this search?",
    "years_experience": "How many years of experience should we use?",
    "locations": "Where do you want to work?",
    "work_mode": "Remote, hybrid, or on-site?",
    "country": "Which country should we search in? Use a 2-letter code like in or us.",
}

ANSWER_SYSTEM = """You update a job-search profile from the candidate's reply.

Return JSON with this exact shape:
{
  "profile_patch": {
    "target_titles": [string, ...] | omit,
    "skills": [string, ...] | omit,
    "years_experience": number | omit,
    "locations": [string, ...] | omit,
    "work_mode": "on-site" | "remote" | "hybrid" | omit,
    "country": string | omit
  },
  "note": string
}

Rules:
- Only include fields the user actually answered.
- country must be ISO 3166-1 alpha-2 lowercase when present.
- Do not invent employers or skills they did not mention.
- note: one short sentence confirming what you changed.
- Return only JSON"""


def profile_snapshot(source: Any) -> dict[str, Any]:
    """Normalize profile fields from a dict or ORM row."""
    get = source.get if isinstance(source, dict) else lambda key, default=None: getattr(source, key, default)
    titles = _coerce_list(get("target_titles"))[:6]
    skills = _coerce_list(get("skills"))[:20]
    locations = _coerce_list(get("locations"))[:6]
    try:
        years = max(0.0, float(get("years_experience") or 0))
    except (TypeError, ValueError):
        years = 0.0
    work_mode = get("work_mode")
    if work_mode not in {"on-site", "remote", "hybrid"}:
        work_mode = "hybrid"
    country = str(get("country") or "").strip().lower()[:2]
    return {
        "target_titles": titles,
        "skills": skills,
        "years_experience": years,
        "locations": locations,
        "work_mode": work_mode,
        "country": country,
        "resume_text": str(get("resume_text") or ""),
    }


def field_is_weak(field: str, value: Any, confidence: float) -> bool:
    if confidence < CONFIDENCE_THRESHOLD:
        return True
    if field in {"target_titles", "skills", "locations"} and not value:
        return True
    if field == "years_experience":
        try:
            years = float(value or 0)
        except (TypeError, ValueError):
            years = 0.0
        if years <= 0:
            return True
    if field == "country" and not value:
        return True
    return False


def heuristic_confidence(draft: dict[str, Any], raw: Any = None) -> dict[str, float]:
    raw_map = raw if isinstance(raw, dict) else {}
    confidence: dict[str, float] = {}
    for field in PROFILE_FIELDS:
        if field in raw_map:
            confidence[field] = _as_confidence(raw_map.get(field), 0.4)
            continue
        value = draft.get(field)
        if field == "target_titles":
            confidence[field] = 0.85 if value else 0.25
        elif field == "skills":
            confidence[field] = 0.85 if len(value or []) >= 4 else 0.45 if value else 0.2
        elif field == "years_experience":
            confidence[field] = 0.8 if float(value or 0) > 0 else 0.2
        elif field == "locations":
            confidence[field] = 0.8 if value else 0.25
        elif field == "work_mode":
            confidence[field] = 0.45 if value == "hybrid" else 0.75
        else:
            confidence[field] = 0.8 if value else 0.2
    return confidence


def normalize_questions(raw: Any, draft: dict[str, Any], confidence: dict[str, float]) -> list[dict[str, str]]:
    by_field: dict[str, str] = {}
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            field = str(item.get("field") or "").strip()
            ask = str(item.get("ask") or "").strip()
            if field in PROFILE_FIELDS and ask:
                by_field[field] = ask
    questions: list[dict[str, str]] = []
    for field in PROFILE_FIELDS:
        if not field_is_weak(field, draft.get(field), confidence.get(field, 0.4)):
            continue
        questions.append({"field": field, "ask": by_field.get(field) or FIELD_QUESTIONS[field]})
    return questions


def normalize_inferences(raw: Any, draft: dict[str, Any]) -> dict[str, dict[str, Any]]:
    raw_map = raw if isinstance(raw, dict) else {}
    inferences: dict[str, dict[str, Any]] = {}
    for field in PROFILE_FIELDS:
        item = raw_map.get(field)
        if isinstance(item, dict) and "value" in item:
            inferences[field] = {
                "value": _coerce_field(field, item.get("value"), draft.get(field)),
                "reason": str(item.get("reason") or "Best guess from your resume.").strip(),
            }
            continue
        inferences[field] = {
            "value": default_inference_value(field, draft),
            "reason": default_inference_reason(field, draft),
        }
    return inferences


def default_inference_value(field: str, draft: dict[str, Any]) -> Any:
    current = draft.get(field)
    if field == "target_titles":
        return current or ["Software Engineer"]
    if field == "skills":
        return current or []
    if field == "years_experience":
        years = float(current or 0)
        return years if years > 0 else 1.0
    if field == "locations":
        return current or []
    if field == "work_mode":
        return current if current in {"on-site", "remote", "hybrid"} else "hybrid"
    if field == "country":
        return current or "us"
    return current


def default_inference_reason(field: str, draft: dict[str, Any]) -> str:
    if field == "target_titles" and not draft.get("target_titles"):
        return "Generic search title until you specify one."
    if field == "years_experience" and float(draft.get("years_experience") or 0) <= 0:
        return "Resume did not state years clearly; using an entry-level default."
    if field == "work_mode":
        return "Defaulting to hybrid until you say otherwise."
    if field == "country" and not draft.get("country"):
        return "Defaulting to us until you pick a country."
    if field == "locations" and not draft.get("locations"):
        return "No city on the resume; leaving locations empty."
    if field == "skills" and not draft.get("skills"):
        return "No concrete skills found; add them if you can."
    return "Taken from your resume."


def apply_field(profile: dict[str, Any], field: str, value: Any) -> dict[str, Any]:
    updated = dict(profile)
    updated[field] = _coerce_field(field, value, profile.get(field))
    return updated


def apply_inference(
    profile: dict[str, Any],
    field: str,
    inferences: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], str]:
    item = inferences.get(field) or {}
    value = item.get("value", default_inference_value(field, profile))
    reason = str(item.get("reason") or default_inference_reason(field, profile))
    return apply_field(profile, field, value), reason


def next_question(
    profile: dict[str, Any],
    confidence: dict[str, float],
    questions: list[dict[str, str]],
    resolved: set[str],
) -> dict[str, str] | None:
    by_field = {item["field"]: item["ask"] for item in questions if item.get("field")}
    for field in PROFILE_FIELDS:
        if field in resolved:
            continue
        if field_is_weak(field, profile.get(field), confidence.get(field, 0.4)):
            return {"field": field, "ask": by_field.get(field) or FIELD_QUESTIONS[field]}
    return None


def build_interview(
    draft: dict[str, Any],
    *,
    confidence: Any = None,
    questions: Any = None,
    inferences: Any = None,
    resolved: list[str] | set[str] | None = None,
    inferred_fields: list[str] | None = None,
) -> dict[str, Any]:
    snapshot = profile_snapshot(draft)
    confidence_map = heuristic_confidence(snapshot, confidence)
    question_list = normalize_questions(questions, snapshot, confidence_map)
    inference_map = normalize_inferences(inferences, snapshot)
    resolved_set = {field for field in (resolved or []) if field in PROFILE_FIELDS}
    question = next_question(snapshot, confidence_map, question_list, resolved_set)
    return {
        "confidence": confidence_map,
        "questions": question_list,
        "inferences": inference_map,
        "question": question["ask"] if question else None,
        "question_field": question["field"] if question else None,
        "resolved_fields": sorted(resolved_set),
        "inferred_fields": [field for field in (inferred_fields or []) if field in PROFILE_FIELDS],
        "done": question is None,
    }


def interview_from_profile(profile: Any) -> dict[str, Any]:
    return build_interview(profile_snapshot(profile))


def interpret_answer(
    profile: dict[str, Any],
    message: str,
    question_field: str | None,
    resume_excerpt: str = "",
) -> tuple[dict[str, Any], str]:
    """Map a free-text reply onto profile fields."""
    payload = {
        "current_profile": {field: profile.get(field) for field in PROFILE_FIELDS},
        "question_field": question_field,
        "user_reply": message,
        "resume_excerpt": resume_excerpt[:2000],
    }
    try:
        raw = chat(
            [
                {"role": "system", "content": ANSWER_SYSTEM},
                {"role": "user", "content": str(payload)},
            ],
            temperature=0.1,
            json_mode=True,
        )
        data = extract_json(raw)
    except Exception:  # noqa: BLE001 — keep the interview moving
        data = {}

    patch_in = data.get("profile_patch") if isinstance(data.get("profile_patch"), dict) else {}
    patch: dict[str, Any] = {}
    for field in PROFILE_FIELDS:
        if field not in patch_in:
            continue
        patch[field] = _coerce_field(field, patch_in.get(field), profile.get(field))

    if not patch and question_field and message.strip():
        patch[question_field] = _coerce_field(question_field, message, profile.get(question_field))

    note = str(data.get("note") or "").strip()
    if not note and patch:
        note = "Updated your profile from that answer."
    if not note:
        note = "I could not map that reply. Try a shorter answer, or skip and I will guess."
    return patch, note


def run_interview_turn(
    *,
    profile: Any,
    action: str,
    message: str = "",
    interview: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str]:
    """Apply answer/skip/confirm and return (profile, interview, assistant_message)."""
    snapshot = profile_snapshot(profile)
    state = interview if isinstance(interview, dict) else {}
    current = build_interview(
        snapshot,
        confidence=state.get("confidence"),
        questions=state.get("questions"),
        inferences=state.get("inferences"),
        resolved=state.get("resolved_fields"),
        inferred_fields=state.get("inferred_fields"),
    )
    resolved = set(current["resolved_fields"])
    inferred = list(current["inferred_fields"])
    question_field = current.get("question_field")
    assistant = ""

    if action == "confirm":
        current = build_interview(
            snapshot,
            confidence=current["confidence"],
            questions=current["questions"],
            inferences=current["inferences"],
            resolved=PROFILE_FIELDS,
            inferred_fields=inferred,
        )
        current["done"] = True
        current["question"] = None
        current["question_field"] = None
        return snapshot, current, "Profile looks good. You can find jobs now."

    if action == "skip" and question_field:
        snapshot, reason = apply_inference(snapshot, question_field, current["inferences"])
        resolved.add(question_field)
        if question_field not in inferred:
            inferred.append(question_field)
        current["confidence"][question_field] = min(current["confidence"].get(question_field, 0.4), 0.55)
        assistant = f"I'll use { _display_value(snapshot.get(question_field)) }. {reason}"
    elif action == "answer":
        reply = (message or "").strip()
        if not reply:
            return snapshot, current, current.get("question") or "Tell me a bit more, or skip and I will guess."
        patch, note = interpret_answer(
            snapshot,
            reply,
            question_field,
            snapshot.get("resume_text") or "",
        )
        for field, value in patch.items():
            snapshot = apply_field(snapshot, field, value)
            resolved.add(field)
            current["confidence"][field] = 1.0
            if field in inferred:
                inferred.remove(field)
        assistant = note
        if question_field and question_field not in patch:
            resolved.add(question_field)

    next_state = build_interview(
        snapshot,
        confidence=current["confidence"],
        questions=current["questions"],
        inferences=current["inferences"],
        resolved=resolved,
        inferred_fields=inferred,
    )
    if next_state.get("question") and action != "confirm":
        if assistant:
            assistant = f"{assistant} {next_state['question']}"
        else:
            assistant = next_state["question"]
    elif action != "confirm":
        assistant = assistant or "That covers the unclear fields. Looks good — find jobs when you are ready."
        next_state["done"] = True
    return snapshot, next_state, assistant


def _as_confidence(value: Any, default: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in value.replace(";", ",").split(",") if part.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def _coerce_field(field: str, value: Any, fallback: Any) -> Any:
    if field in {"target_titles", "skills", "locations"}:
        items = _coerce_list(value)
        return items if items or value == [] else _coerce_list(fallback)
    if field == "years_experience":
        try:
            if isinstance(value, str):
                cleaned = "".join(ch for ch in value if ch.isdigit() or ch == ".")
                return max(0.0, float(cleaned or 0))
            return max(0.0, float(value))
        except (TypeError, ValueError):
            try:
                return max(0.0, float(fallback or 0))
            except (TypeError, ValueError):
                return 0.0
    if field == "work_mode":
        text = str(value or "").strip().lower().replace("onsite", "on-site").replace("on site", "on-site")
        if text in {"on-site", "remote", "hybrid"}:
            return text
        return fallback if fallback in {"on-site", "remote", "hybrid"} else "hybrid"
    if field == "country":
        code = str(value or "").strip().lower()[:2]
        if len(code) == 2 and code.isalpha():
            return code
        fallback_code = str(fallback or "").strip().lower()[:2]
        return fallback_code if len(fallback_code) == 2 else ""
    return value if value is not None else fallback


def _display_value(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value) or "none"
    return str(value)
