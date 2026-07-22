from __future__ import annotations

import json

from job_agent.llm import chat, extract_json
from job_agent.models import CompanyResearch, Critique

DRAFT_SYSTEM = """You are a professional cover-letter writer. Write specific, concrete, non-generic
cover letters that reference real facts about the company and map the candidate's
actual experience to the role's requirements. Avoid filler phrases like "I am a hard
worker" — be concrete instead.

Rules:
- Reference at least one specific company fact from the research
- Map at least 2-3 of the candidate's real experiences to the role's stated requirements
- Do not invent experience the candidate doesn't have
- Keep the letter 250-350 words
- Return only the cover letter text (no markdown fences, no commentary)"""

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

REVISE_SYSTEM = """You revise cover letters based on specific critique feedback. Fix only the flagged
issues; keep what already works.

Rules:
- Do not invent experience beyond the resume
- Keep length around 250-350 words
- Return only the revised letter text (no markdown fences, no commentary)"""


def draft_cover_letter(
    research: CompanyResearch,
    job_description: str,
    resume_text: str,
) -> str:
    """Writer Step 1: draft a tailored cover letter."""
    user = f"""Write a tailored cover letter (250-350 words) using the information below.

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
candidate doesn't have."""

    return chat(
        [
            {"role": "system", "content": DRAFT_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.5,
    )


def critique_cover_letter(
    job_description: str,
    resume_text: str,
    draft: str,
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

Draft cover letter to review:
\"\"\"
{draft}
\"\"\"

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
    draft: str,
    critique: Critique,
    resume_text: str,
) -> str:
    """Writer Step 3: revise only when critique flags issues."""
    user = f"""Original draft:
\"\"\"
{draft}
\"\"\"

Critique feedback to address:
{json.dumps(critique.model_dump(), indent=2)}

Candidate resume (do not invent anything beyond this):
\"\"\"
{resume_text}
\"\"\"

Rewrite the cover letter addressing the feedback. Return only the revised letter text."""

    return chat(
        [
            {"role": "system", "content": REVISE_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
    )


def write_cover_letter(
    research: CompanyResearch,
    job_description: str,
    resume_text: str,
) -> tuple[str, Critique, str, bool]:
    """Full Writer agent: draft → critique → conditional revise.

    Returns (draft, critique, final_letter, was_revised).
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
