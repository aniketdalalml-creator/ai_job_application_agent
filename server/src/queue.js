import { runPipeline } from "./agents/pipeline.js";
import { appendEvent, getRun, saveRun } from "./store.js";

/** @type {string[]} */
const queue = [];
let processing = false;

/**
 * @param {string} runId
 */
function enqueue(runId) {
  queue.push(runId);
  void processQueue();
}

async function processQueue() {
  if (processing) return;
  processing = true;

  while (queue.length) {
    const runId = queue.shift();
    if (!runId) continue;
    await processRun(runId);
  }

  processing = false;
}

/**
 * @param {string} runId
 */
async function processRun(runId) {
  const run = getRun(runId);
  if (!run) return;

  run.status = "running";
  run.startedAt = new Date().toISOString();
  saveRun(run);

  try {
    const result = await runPipeline({
      companyName: run.companyName,
      jobDescription: run.jobDescription,
      resumeText: run.resumeText,
      onEvent: (event) => {
        appendEvent(runId, event);
      },
    });

    run.result = result;
    run.status = "completed";
    run.finishedAt = new Date().toISOString();
    saveRun(run);
  } catch (error) {
    run.status = "failed";
    run.error = error instanceof Error ? error.message : String(error);
    run.finishedAt = new Date().toISOString();
    appendEvent(runId, {
      type: "error",
      message: run.error,
      timestamp: new Date().toISOString(),
    });
    saveRun(run);
  }
}

export { enqueue };
