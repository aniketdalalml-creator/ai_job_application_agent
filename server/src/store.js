/** @typedef {'queued' | 'running' | 'completed' | 'failed'} RunStatus */

/** @typedef {{
 *   id: string;
 *   status: RunStatus;
 *   companyName: string;
 *   jobDescription: string;
 *   resumeText: string;
 *   createdAt: string;
 *   startedAt?: string;
 *   finishedAt?: string;
 *   error?: string;
 *   result?: import('./agents/pipeline.js').PipelineResult;
 *   events: import('./agents/pipeline.js').TraceEvent[];
 * }} ApplicationRun */

/** @type {Map<string, ApplicationRun>} */
const runs = new Map();

/** @param {ApplicationRun} run */
export function saveRun(run) {
  runs.set(run.id, run);
}

/** @param {string} id */
export function getRun(id) {
  return runs.get(id);
}

export function listRuns() {
  return [...runs.values()].sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
}

/** @param {string} id */
export function appendEvent(id, event) {
  const run = runs.get(id);
  if (!run) return;
  run.events.push(event);
}
