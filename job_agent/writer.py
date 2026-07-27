from __future__ import annotations

import json
from typing import Any

from job_agent.llm import chat, extract_json
from job_agent.models import CompanyResearch, Critique

DRAFT_SYSTEM = """You are a professional cover-letter writer. Write specific, concrete, non-generic
application materials that reference real facts about the company and map the candidate's
actual experience to the role's requirements. Avoid filler phrases like "I am a hard
worker" — be concrete instead.

Return JSON with this exact shape:
{
  "coverLetter": string,
  "resumeBullets": [string, ...]
}

Rules:
- coverLetter: 250-350 words, reference at least one specific company fact and map 2-3 resume experiences to role requirements
- resumeBullets: 4-6 tailored bullets for this role/company (one line each, strong action verbs)
- Do not invent experience the candidate doesn't have
- Return only the JSON object (no markdown fences, no commentary)"""

CRITIQUE_SYSTEM = """You are a critical reviewer of cover letters. You check for genericness,
unsupported claims, and missed alignment with the job description.

Return JSON with this exact shape:
{
  "hasIssues": boolean,
  "issues": [string, ...],
  "unsupportedClaims": [string, ...],
  "missingAlignment": [string, ...]
}

Be strict but fair. Flag claims not grounded in the resume. Flag missing mappings to
important JD requirements. If the letter is solid, set hasIssues to false and use empty lists."""

REVISE_SYSTEM = """You revise job application materials based on specific critique feedback. Fix only the flagged
issues; keep what already works.

Return JSON with this exact shape:
{
  "coverLetter": string,
  "resumeBullets": [string, ...]
}

Rules:
- Do not invent experience beyond the resume
- Keep cover letter around 250-350 words
- Return only the JSON object (no markdown fences, no commentary)"""


def draft_cover_letter(
    research: CompanyResearch,
    job_description: str,
    resume_text: str,
) -> dict[str, Any]:
    """Writer Step 1: draft tailored application materials."""
    user = f"""Write tailored application materials using the information below.

Company research (structured):
{research.model_dump_json(indent=2)}

Job description:
\"\"\"
{job_description}
\"\"\"

Candidate resume:
\"\"\"
{resume_text}
\"\"\"

Reference at least one specific company fact and map at least 2-3 of the candidate's
real experiences to the role's stated requirements. Do not invent experience the
candidate doesn't have. Return only the JSON object."""

    raw = chat(
        [
            {"role": "system", "content": DRAFT_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
        json_mode=True,
    )
    return extract_json(raw)


def critique_cover_letter(
    job_description: str,
    resume_text: str,
    draft: dict[str, Any],
) -> Critique:
    """Writer Step 2: self-critique the draft against JD + resume."""
    user = f"""Job description:
\"\"\"
{job_description}
\"\"\"

Candidate resume (ground truth of real experience):
\"\"\"
{resume_text}
\"\"\"

Draft application materials to review:
{json.dumps(draft, indent=2)}

Return only the JSON object."""

    raw = chat(
        [
            {"role": "system", "content": CRITIQUE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
        json_mode=True,
    )
    return Critique.model_validate(extract_json(raw))


def revise_cover_letter(
    draft: dict[str, Any],
    critique: Critique,
    resume_text: str,
) -> dict[str, Any]:
    """Writer Step 3: revise only when critique flags issues."""
    user = f"""Original draft:
{json.dumps(draft, indent=2)}

Critique feedback to address:
{json.dumps(critique.model_dump(), indent=2)}

Candidate resume (do not invent anything beyond this):
\"\"\"
{resume_text}
\"\"\"

Rewrite the application materials addressing the feedback. Return only the JSON object."""

    raw = chat(
        [
            {"role": "system", "content": REVISE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
        json_mode=True,
    )
    return extract_json(raw)


def write_cover_letter(
    research: CompanyResearch,
    job_description: str,
    resume_text: str,
) -> tuple[dict[str, Any], Critique, dict[str, Any], bool]:
    """Full Writer agent: draft → critique → conditional revise.

    Returns (draft, critique, final_materials, was_revised).
    """
    draft = draft_cover_letter(research, job_description, resume_text)
    critique = critique_cover_letter(job_description, resume_text, draft)

    needs_revision = critique.hasIssues or bool(
        critique.issues or critique.unsupportedClaims or critique.missingAlignment
    )

    if needs_revision:
        final = revise_cover_letter(draft, critique, resume_text)
        return draft, critique, final, True

    return draft, critique, draft, False
