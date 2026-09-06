from __future__ import annotations

from dataclasses import dataclass

from ddgs import DDGS

from backend.app.integrations.llm import Settings, get_settings
from backend.app.integrations.llm import chat, extract_json
from backend.app.ai.models import CompanyResearch

RESEARCH_SYSTEM = """You are a research assistant. Use the provided web search results to find recent, relevant
information about the given company: recent news, products, mission/values, and
anything notable in the last 6-12 months. Be factual and concise. Do not invent facts
not supported by the search results. If search results are thin, say so explicitly."""

HANDOFF_SYSTEM = """You convert raw research notes and a job description into a clean structured JSON
object for another AI agent to use when drafting a job application.

Return JSON with this exact shape:
{
  "companyName": string,
  "companyFacts": [string, ...],
  "roleRequirements": [string, ...],
  "cultureSignals": [string, ...],
  "sources": [string, ...]
}

Rules:
- companyFacts: 3-5 concrete, specific facts grounded in the research notes
- roleRequirements: 4-6 key requirements extracted from the job description
- cultureSignals: 2-3 signals about values/culture from research or JD
- sources: source names/domains from the research, or [] if none
- Do not invent unsupported company facts"""


@dataclass
class SearchBundle:
    text: str
    sources: list[str]


def web_search(company_name: str, *, max_results: int | None = None) -> SearchBundle:
    """Search the web for recent company information."""
    settings = get_settings()
    limit = max_results or settings.max_search_results
    queries = [
        f"{company_name} company overview products services",
        f"{company_name} recent news 2025 2026",
        f"{company_name} mission values culture",
    ]

    seen_urls: set[str] = set()
    lines: list[str] = []
    sources: list[str] = []

    with DDGS() as ddgs:
        for query in queries:
            try:
                results = list(ddgs.text(query, max_results=max(3, limit // 2)))
            except Exception as exc:  # noqa: BLE001 — keep pipeline resilient
                lines.append(f"[search error for '{query}']: {exc}")
                continue

            for item in results:
                url = (item.get("href") or item.get("link") or "").strip()
                title = (item.get("title") or "").strip()
                body = (item.get("body") or item.get("snippet") or "").strip()
                if not body:
                    continue
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                    sources.append(_domain(url))
                lines.append(f"- {title}\n  URL: {url or 'n/a'}\n  {body}")

            if len(lines) >= limit * 2:
                break

    # Deduplicate source domains while preserving order
    unique_sources = list(dict.fromkeys(sources))
    text = "\n".join(lines) if lines else f"No web results found for {company_name}."
    return SearchBundle(text=text, sources=unique_sources)


def _domain(url: str) -> str:
    try:
        from urllib.parse import urlparse

        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:  # noqa: BLE001
        return url


def summarize_search(company_name: str, search_text: str) -> str:
    """Step 1: turn raw search hits into concise research notes."""
    user = f"""Research this company for a job application: {company_name}.
Find recent news, main products/services, and culture or values signals.

Web search results:
\"\"\"
{search_text}
\"\"\"

Write concise factual research notes (bullet points). Cite source domains inline when possible."""
    return chat(
        [
            {"role": "system", "content": RESEARCH_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
    )


def structure_handoff(
    company_name: str,
    research_notes: str,
    job_description: str,
    sources: list[str] | None = None,
) -> CompanyResearch:
    """Step 2: convert notes + JD into structured JSON for the Writer."""
    source_hint = ", ".join(sources or []) or "(none)"
    user = f"""Raw research notes about the company:
\"\"\"
{research_notes}
\"\"\"

Known source domains from search: {source_hint}

Job description:
\"\"\"
{job_description}
\"\"\"

Company name: {company_name}

Return only the JSON object."""

    raw = chat(
        [
            {"role": "system", "content": HANDOFF_SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
        json_mode=True,
    )
    data = extract_json(raw)
    if not data.get("companyName"):
        data["companyName"] = company_name
    if not data.get("sources") and sources:
        data["sources"] = sources[:8]
    return CompanyResearch.model_validate(data)


def research_company(
    company_name: str,
    job_description: str,
    *,
    settings: Settings | None = None,
) -> tuple[CompanyResearch, str]:
    """Full Researcher agent: web search → notes → structured handoff.

    Returns (structured_research, raw_notes).
    """
    _ = settings or get_settings()
    bundle = web_search(company_name)
    notes = summarize_search(company_name, bundle.text)
    structured = structure_handoff(
        company_name,
        notes,
        job_description,
        sources=bundle.sources,
    )
    return structured, notes
