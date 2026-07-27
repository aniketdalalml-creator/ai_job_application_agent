import { createMessage, extractJson } from "./claude.js";

const DRAFT_SYSTEM = `You are the Writer agent in a multi-agent job application pipeline.

Write specific, grounded application materials using the structured company research and the candidate resume.
Avoid generic filler. Do not invent experience beyond the resume.

Return ONLY JSON (no markdown fences) with this exact shape:
{
  "coverLetter": string,
  "resumeBullets": [string, ...]
}

Rules:
- coverLetter: 250-350 words, references at least one company fact and maps 2-3 resume experiences to role requirements
- resumeBullets: 4-6 tailored bullets for this role/company (each bullet one line, strong action verbs, quantified where resume supports it)`;

const CRITIQUE_SYSTEM = `You critique job application drafts for generic language, unsupported claims, and JD misalignment.

Return ONLY JSON with this exact shape:
{
  "hasIssues": boolean,
  "issues": [string, ...],
  "unsupportedClaims": [string, ...],
  "missingAlignment": [string, ...]
}`;

const REVISE_SYSTEM = `You revise job application materials based on critique feedback.
Fix flagged issues only. Do not invent resume experience.

Return ONLY JSON with this exact shape:
{
  "coverLetter": string,
  "resumeBullets": [string, ...]
}`;

/**
 * @param {Record<string, unknown>} research
 * @param {string} jobDescription
 * @param {string} resumeText
 */
async function draftMaterials(research, jobDescription, resumeText) {
  const response = await createMessage({
    system: DRAFT_SYSTEM,
    messages: [
      {
        role: "user",
        content: `Company research (structured):
${JSON.stringify(research, null, 2)}

Job description:
"""
${jobDescription}
"""

Candidate resume:
"""
${resumeText}
"""`,
      },
    ],
    temperature: 0.5,
  });

  const text = response.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n");

  return extractJson(text);
}

/**
 * @param {string} jobDescription
 * @param {string} resumeText
 * @param {Record<string, unknown>} draft
 */
async function critiqueMaterials(jobDescription, resumeText, draft) {
  const response = await createMessage({
    system: CRITIQUE_SYSTEM,
    messages: [
      {
        role: "user",
        content: `Job description:
"""
${jobDescription}
"""

Resume (ground truth):
"""
${resumeText}
"""

Draft materials:
${JSON.stringify(draft, null, 2)}`,
      },
    ],
    temperature: 0.1,
  });

  const text = response.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n");

  return extractJson(text);
}

/**
 * @param {Record<string, unknown>} draft
 * @param {Record<string, unknown>} critique
 * @param {string} resumeText
 */
async function reviseMaterials(draft, critique, resumeText) {
  const response = await createMessage({
    system: REVISE_SYSTEM,
    messages: [
      {
        role: "user",
        content: `Original draft:
${JSON.stringify(draft, null, 2)}

Critique:
${JSON.stringify(critique, null, 2)}

Resume (do not invent beyond this):
"""
${resumeText}
"""`,
      },
    ],
    temperature: 0.4,
  });

  const text = response.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n");

  return extractJson(text);
}

/**
 * @param {Record<string, unknown>} research
 * @param {string} jobDescription
 * @param {string} resumeText
 * @param {(event: import('./pipeline.js').TraceEvent) => void} emit
 */
export async function runWriter(research, jobDescription, resumeText, emit) {
  emit({
    type: "agent_start",
    agent: "writer",
    message: "Drafting cover letter and tailored resume bullets",
    timestamp: new Date().toISOString(),
  });

  const draft = await draftMaterials(research, jobDescription, resumeText);

  emit({
    type: "draft",
    agent: "writer",
    message: "Initial draft complete",
    payload: draft,
    timestamp: new Date().toISOString(),
  });

  const critique = await critiqueMaterials(jobDescription, resumeText, draft);

  emit({
    type: "critique",
    agent: "writer",
    message: critique.hasIssues ? "Critique flagged issues" : "Draft passed critique",
    payload: critique,
    timestamp: new Date().toISOString(),
  });

  const needsRevision =
    critique.hasIssues ||
    (Array.isArray(critique.issues) && critique.issues.length > 0) ||
    (Array.isArray(critique.unsupportedClaims) && critique.unsupportedClaims.length > 0) ||
    (Array.isArray(critique.missingAlignment) && critique.missingAlignment.length > 0);

  let finalMaterials = draft;
  let revised = false;

  if (needsRevision) {
    emit({
      type: "revise",
      agent: "writer",
      message: "Revising materials based on critique",
      timestamp: new Date().toISOString(),
    });
    finalMaterials = await reviseMaterials(draft, critique, resumeText);
    revised = true;
  }

  emit({
    type: "agent_complete",
    agent: "writer",
    message: revised ? "Revision complete" : "Using draft as final output",
    payload: finalMaterials,
    timestamp: new Date().toISOString(),
  });

  return { draft, critique, finalMaterials, revised };
}
