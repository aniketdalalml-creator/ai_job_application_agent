import { createMessage, extractJson } from "./claude.js";
import { WEB_SEARCH_TOOL, webSearch } from "../tools/webSearch.js";

const RESEARCHER_SYSTEM = `You are the Researcher agent in a multi-agent job application pipeline.

Use the web_search tool to gather recent, factual information about the target company and role context.
Run multiple focused searches (overview/products, recent news, culture/mission) before you finish.

When you have enough information, respond with ONLY a JSON object (no markdown fences) in this exact shape:
{
  "companyName": string,
  "companyFacts": [string, ...],
  "roleRequirements": [string, ...],
  "cultureSignals": [string, ...],
  "sources": [string, ...],
  "researchNotes": string
}

Rules:
- companyFacts: 3-5 concrete facts grounded in search results
- roleRequirements: 4-6 requirements extracted from the job description
- cultureSignals: 2-3 culture/value signals
- sources: source domains from search results
- researchNotes: concise bullet-style notes for debugging
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

  /** @type {import('@anthropic-ai/sdk').MessageParam[]} */
  const messages = [
    {
      role: "user",
      content: `Research this company for a job application.

Company: ${companyName}

Job description:
"""
${jobDescription}
"""

Use web_search as needed, then return the final JSON handoff object.`,
    },
  ];

  const searchLog = [];
  let structured = null;

  for (let turn = 0; turn < 8; turn += 1) {
    const response = await createMessage({
      system: RESEARCHER_SYSTEM,
      tools: [WEB_SEARCH_TOOL],
      messages,
      temperature: 0.2,
    });

    const toolUses = response.content.filter((block) => block.type === "tool_use");
    const textBlocks = response.content.filter((block) => block.type === "text");

    if (toolUses.length) {
      messages.push({ role: "assistant", content: response.content });

      /** @type {import('@anthropic-ai/sdk').ToolResultBlockParam[]} */
      const toolResults = [];

      for (const toolUse of toolUses) {
        if (toolUse.name !== "web_search") continue;
        const query =
          typeof toolUse.input === "object" &&
          toolUse.input &&
          "query" in toolUse.input &&
          typeof toolUse.input.query === "string"
            ? toolUse.input.query
            : `${companyName} company`;

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

        toolResults.push({
          type: "tool_result",
          tool_use_id: toolUse.id,
          content: bundle.text,
        });
      }

      messages.push({ role: "user", content: toolResults });
      continue;
    }

    const text = textBlocks.map((block) => block.text).join("\n").trim();
    if (!text) {
      throw new Error("Researcher returned an empty response");
    }

    structured = extractJson(text);
    if (!structured.companyName) structured.companyName = companyName;
    if (!structured.sources?.length) {
      structured.sources = [
        ...new Set(searchLog.flatMap((entry) => entry.results.map((item) => item.url))),
      ]
        .map((url) => {
          try {
            return new URL(url).hostname.replace(/^www\./, "");
          } catch {
            return url;
          }
        })
        .filter(Boolean)
        .slice(0, 8);
    }

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

  throw new Error("Researcher exceeded maximum tool-calling turns");
}
