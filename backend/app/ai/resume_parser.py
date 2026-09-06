"""Extract text from a resume file and turn it into profile fields."""

from __future__ import annotations

import io
import re
from typing import Any

from backend.app.integrations.llm import chat, extract_json
from backend.app.ai.profile_interview import build_interview

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}
MAX_RESUME_BYTES = 2 * 1024 * 1024

EXTRACT_SYSTEM = """You extract a job-seeker profile from resume text.

Return JSON with this exact shape:
{
  "target_titles": [string, ...],
  "skills": [string, ...],
  "years_experience": number,
  "locations": [string, ...],
  "work_mode": "on-site" | "remote" | "hybrid",
  "country": string,
  "confidence": {
    "target_titles": number,
    "skills": number,
    "years_experience": number,
    "locations": number,
    "work_mode": number,
    "country": number
  },
  "questions": [{"field": string, "ask": string}, ...],
  "inferences": {
    "target_titles": {"value": [string, ...], "reason": string},
    "skills": {"value": [string, ...], "reason": string},
    "years_experience": {"value": number, "reason": string},
    "locations": {"value": [string, ...], "reason": string},
    "work_mode": {"value": "on-site" | "remote" | "hybrid", "reason": string},
    "country": {"value": string, "reason": string}
  }
}

Rules:
- target_titles: 1-4 likely job titles this person would search for
- skills: 6-16 concrete tools or skills from the resume
- years_experience: total professional years; 0 if unclear
- locations: cities or regions mentioned, or empty
- work_mode: infer from the resume; default hybrid
- country: ISO 3166-1 alpha-2 lowercase (us, in, gb, ...). Empty if unknown
- confidence: 0-1 for each field. Low if guessed, missing, or conflicting
- questions: only for unclear fields; one short ask each
- inferences: best guess to use if the user skips that question
- Do not invent employers or skills that are not in the text
- Return only JSON"""

COUNTRY_HINTS = {
    "india": "in",
    "bengaluru": "in",
    "bangalore": "in",
    "mumbai": "in",
    "hyderabad": "in",
    "delhi": "in",
    "pune": "in",
    "united states": "us",
    "usa": "us",
    "u.s.": "us",
    "united kingdom": "gb",
    "london": "gb",
    "england": "gb",
    "canada": "ca",
    "toronto": "ca",
    "australia": "au",
    "germany": "de",
    "singapore": "sg",
}


def _suffix(filename: str) -> str:
    name = (filename or "").strip().lower()
    dot = name.rfind(".")
    return name[dot:] if dot != -1 else ""


def extract_text(filename: str, data: bytes) -> str:
    """Pull plain text from a PDF, DOCX, or TXT upload."""
    suffix = _suffix(filename)
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload a PDF, DOCX, or TXT resume.")
    if suffix == ".pdf":
        return _extract_pdf(data)
    if suffix == ".docx":
        return _extract_docx(data)
    return _extract_txt(data)


def _extract_txt(data: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "latin-1"):
        try:
            text = data.decode(encoding)
            if text.strip():
                return text.strip()
        except UnicodeDecodeError:
            continue
    raise ValueError("Could not read that text file.")


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts = [(page.extract_text() or "") for page in reader.pages]
    text = "\n".join(parts).strip()
    if not text:
        raise ValueError("No text found in that PDF. Try a text-based resume, not a scanned image.")
    return text


def _extract_docx(data: bytes) -> str:
    from docx import Document

    document = Document(io.BytesIO(data))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    if not text:
        raise ValueError("No text found in that Word document.")
    return text


def _coerce_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;\n]", value) if part.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def _infer_country(text: str, locations: list[str], extracted: str) -> str:
    code = (extracted or "").strip().lower()[:2]
    if len(code) == 2 and code.isalpha():
        return code
    haystack = " ".join([text[:2000], *locations]).lower()
    for needle, mapped in COUNTRY_HINTS.items():
        if needle in haystack:
            return mapped
    return ""


def parse_resume_profile(resume_text: str) -> dict[str, Any]:
    """LLM extraction of search fields, with a safe empty fallback."""
    try:
        raw = chat(
            [
                {"role": "system", "content": EXTRACT_SYSTEM},
                {"role": "user", "content": resume_text[:12000]},
            ],
            temperature=0.1,
            json_mode=True,
        )
        data = extract_json(raw)
    except Exception:  # noqa: BLE001 — upload should still save resume text
        data = {}

    titles = _coerce_list(data.get("target_titles"))[:6]
    skills = _coerce_list(data.get("skills"))[:20]
    locations = _coerce_list(data.get("locations"))[:6]
    try:
        years = max(0.0, float(data.get("years_experience") or 0))
    except (TypeError, ValueError):
        years = 0.0
    work_mode = data.get("work_mode") if data.get("work_mode") in {"on-site", "remote", "hybrid"} else "hybrid"
    country = _infer_country(resume_text, locations, str(data.get("country") or ""))
    draft = {
        "target_titles": titles,
        "skills": skills,
        "years_experience": years,
        "locations": locations,
        "work_mode": work_mode,
        "country": country,
        "resume_text": resume_text,
    }
    return {
        **draft,
        "interview": build_interview(
            draft,
            confidence=data.get("confidence"),
            questions=data.get("questions"),
            inferences=data.get("inferences"),
        ),
    }
