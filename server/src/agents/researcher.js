import { chatCompletion, extractJson } from "./llm.js";
import { webSearch } from "../tools/webSearch.js";

const RESEARCH_SYSTEM = `You are a research assistant. Use the provided web search results to find recent, relevant
information about the given company: recent news, products, mission/values, and anything notable.
Be factual and concise. Do not invent facts not supported by the search results.`;

const HANDOFF_SYSTEM = `You convert raw research notes and a job description into a clean structured JSON object
for another AI agent to use when drafting a job application.

Return JSON with this exact shape:
{
  "companyName": string,
  "companyFacts": [string, ...],
  "roleRequirements": [string, ...],
  "cultureSignals": [string, ...],
  "sources": [string, ...],
  "researchNotes": string
}

Rules:
- companyFacts: 3-5 concrete facts grounded in the research notes
- roleRequirements: 4-6 key requirements extracted from the job description
- cultureSignals: 2-3 culture/value signals
- sources: source domains from research
- researchNotes: concise bullet-style notes
- Do not invent unsupported company facts`;

/**
 * @param {string} companyName
 * @param {string} jobDescription
 * @param {(event: import('./pipeline.js').TraceEvent) => void} emit
 */
export async function runResearcher(companyName, jobDescription, emit) {
  emit({
    type: "agent_start",
    agent: "researcher",
    message: `Starting web research for ${companyName}`,
    timestamp: new Date().toISOString(),
  });

  const queries = [
    `${companyName} company overview products services`,
    `${companyName} recent news 2025 2026`,
    `${companyName} mission values culture`,
  ];

  const searchLog = [];

  for (const query of queries) {
    emit({
      type: "tool_call",
      agent: "researcher",
      message: `web_search("${query}")`,
      payload: { query },
      timestamp: new Date().toISOString(),
    });

    const bundle = await webSearch(query);
    searchLog.push(bundle);

    emit({
      type: "tool_result",
      agent: "researcher",
      message: `Found ${bundle.results.length} result(s) for "${query}"`,
      payload: bundle,
      timestamp: new Date().toISOString(),
    });
  }

  const searchText = searchLog.map((entry) => entry.text).join("\n\n");
  const sources = [
    ...new Set(searchLog.flatMap((entry) => entry.results.map((item) => item.url))),
  ]
    .map((url) => {
      try {
        return new URL(url).hostname.replace(/^www\./, "");
      } catch {
        return url;
      }
    })
    .filter(Boolean);

  const notes = await chatCompletion({
    system: RESEARCH_SYSTEM,
    messages: [
      {
        role: "user",
        content: `Research this company for a job application: ${companyName}.

Web search results:
"""
${searchText}
"""

Write concise factual research notes (bullet points). Cite source domains inline when possible.`,
      },
    ],
    temperature: 0.2,
  });

  const structured = extractJson(
    await chatCompletion({
      system: HANDOFF_SYSTEM,
      messages: [
        {
          role: "user",
          content: `Raw research notes:
"""
${notes}
"""

Known source domains: ${sources.slice(0, 8).join(", ") || "(none)"}

Job description:
"""
${jobDescription}
"""

Company name: ${companyName}

Return only the JSON object.`,
        },
      ],
      temperature: 0.1,
      jsonMode: true,
    }),
  );

  if (!structured.companyName) structured.companyName = companyName;
  if (!structured.sources?.length) structured.sources = sources.slice(0, 8);
  if (!structured.researchNotes) structured.researchNotes = notes;

  emit({
    type: "handoff",
    agent: "researcher",
    message: "Structured JSON handoff ready for Writer",
    payload: structured,
    timestamp: new Date().toISOString(),
  });

  emit({
    type: "agent_complete",
    agent: "researcher",
    message: "Research complete",
    timestamp: new Date().toISOString(),
  });

  return { research: structured, searchLog };
}
