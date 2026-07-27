import { runResearcher } from "./researcher.js";
import { runWriter } from "./writer.js";

/**
 * @typedef {{
 *   type: string;
 *   agent?: string;
 *   message: string;
 *   payload?: unknown;
 *   timestamp: string;
 * }} TraceEvent
 */

/**
 * @typedef {{
 *   research: Record<string, unknown>;
 *   draft: Record<string, unknown>;
 *   critique: Record<string, unknown>;
 *   finalMaterials: Record<string, unknown>;
 *   revised: boolean;
 * }} PipelineResult
 */

/**
 * @param {{
 *   companyName: string;
 *   jobDescription: string;
 *   resumeText: string;
 *   onEvent?: (event: TraceEvent) => void;
 * }} input
 * @returns {Promise<PipelineResult>}
 */
export async function runPipeline({ companyName, jobDescription, resumeText, onEvent }) {
  const emit = (event) => {
    onEvent?.(event);
  };

  emit({
    type: "pipeline_start",
    message: `Pipeline started for ${companyName}`,
    timestamp: new Date().toISOString(),
  });

  const { research } = await runResearcher(companyName, jobDescription, emit);
  const writerResult = await runWriter(research, jobDescription, resumeText, emit);

  const result = {
    research,
    draft: writerResult.draft,
    critique: writerResult.critique,
    finalMaterials: writerResult.finalMaterials,
    revised: writerResult.revised,
  };

  emit({
    type: "pipeline_complete",
    message: "Pipeline finished",
    payload: result,
    timestamp: new Date().toISOString(),
  });

  return result;
}
