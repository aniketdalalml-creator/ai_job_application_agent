const WORKFLOW_STEPS = [
  { id: "research", label: "Company research", detail: "Web search and structured notes" },
  { id: "handoff", label: "Research handoff", detail: "Facts ready for the writer" },
  { id: "draft", label: "Draft materials", detail: "Cover letter and resume bullets" },
  { id: "critique", label: "Self-critique", detail: "Check claims against the resume" },
  { id: "revise", label: "Revision pass", detail: "Fix only flagged issues" },
  { id: "complete", label: "Package ready", detail: "Materials saved to your tracker" },
];

function stepState(stepId, events, runStatus) {
  const types = events.map((event) => event.type);
  const order = WORKFLOW_STEPS.map((step) => step.id);

  const completed = {
    research: types.some((type) => type === "tool_result" || type === "handoff"),
    handoff: types.includes("handoff"),
    draft: types.includes("draft"),
    critique: types.includes("critique"),
    revise: types.includes("revise") || (types.includes("critique") && runStatus === "completed"),
    complete: runStatus === "completed" || runStatus === "ready",
  };

  const firstIncomplete = order.find((id) => !completed[id]);
  if (completed[stepId]) return "done";
  if (firstIncomplete === stepId) return "active";
  return "pending";
}

function progressPercent(events, runStatus) {
  const states = WORKFLOW_STEPS.map((step) => stepState(step.id, events, runStatus));
  const doneCount = states.filter((state) => state === "done").length;
  if (runStatus === "completed" || runStatus === "ready") return 100;
  return Math.min(99, Math.round((doneCount / WORKFLOW_STEPS.length) * 100));
}

export default function ProcessingView({ companyName, events, runStatus, error }) {
  const progress = progressPercent(events, runStatus);
  const activeStep = WORKFLOW_STEPS.find((step) => stepState(step.id, events, runStatus) === "active");
  const failed = runStatus === "failed" || Boolean(error);

  return (
    <div className="mx-auto max-w-content space-y-8">
      {failed ? (
        <div className="rounded-2xl border border-error/30 bg-error-container px-4 py-3 text-[13px] font-medium text-error">
          {error || "This run failed. Check the event log below."}
        </div>
      ) : null}

      <div className="space-y-3">
        <div className="inline-flex items-center gap-2 rounded-full bg-primary-fixed px-3 py-1 text-[12px] font-semibold text-primary">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
          Live optimization
        </div>
        <h2 className="max-w-2xl text-[36px] font-bold leading-tight tracking-tight">
          Preparing materials for {companyName}
        </h2>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div className="institutional-panel h-full p-6">
            <div className="mb-6 flex items-center justify-between">
              <h3 className="text-[14px] font-semibold">Agent workflow</h3>
              <span className="status-running">{runStatus}</span>
            </div>
            <div className="relative space-y-5">
              <div className="absolute bottom-2 left-[13px] top-2 w-px bg-outline-variant" />
              {WORKFLOW_STEPS.map((step) => {
                const state = stepState(step.id, events, runStatus);
                return (
                  <div key={step.id} className={`relative flex items-start gap-4 ${state === "pending" ? "opacity-40" : ""}`}>
                    <div
                      className={`z-10 flex h-7 w-7 items-center justify-center rounded-full ${
                        state === "done"
                          ? "bg-primary text-on-primary"
                          : state === "active"
                            ? "border border-primary bg-surface-container-lowest text-primary"
                            : "border border-outline-variant bg-surface-container text-outline"
                      }`}
                    >
                      {state === "done" ? (
                        <span className="material-symbols-outlined text-[14px]">check</span>
                      ) : state === "active" ? (
                        <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
                      ) : (
                        <span className="material-symbols-outlined text-[14px]">more_horiz</span>
                      )}
                    </div>
                    <div className="flex-1 pt-0.5">
                      <p className={`text-[13px] font-semibold ${state === "active" ? "text-primary" : "text-on-surface"}`}>
                        {step.label}
                      </p>
                      <p className="mt-0.5 text-[12px] text-on-surface-variant">{step.detail}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4 lg:col-span-7">
          <div className="institutional-panel flex flex-1 flex-col items-center justify-center p-10 text-center">
            <div className="mb-6 flex h-36 w-36 items-center justify-center rounded-full bg-primary-fixed text-primary">
              <div>
                <span className="text-[40px] font-bold">{progress}</span>
                <span className="text-[14px] font-semibold">%</span>
              </div>
            </div>
            <h4 className="text-[18px] font-semibold">
              {activeStep ? activeStep.label : "Finalizing package"}
            </h4>
            <p className="mt-2 max-w-sm text-[13px] text-on-surface-variant">
              {activeStep
                ? `Working on ${activeStep.label.toLowerCase()} for ${companyName}.`
                : "Saving the application package."}
            </p>
            <div className="relative mt-6 h-2 w-full max-w-sm overflow-hidden rounded-full bg-surface-container">
              <div className="absolute left-0 top-0 h-full rounded-full bg-primary transition-all duration-700" style={{ width: `${progress}%` }} />
            </div>
          </div>

          <div className="h-48 overflow-hidden rounded-2xl bg-console p-5">
            <p className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-white/50">Event log</p>
            <div className="space-y-1.5 overflow-y-auto pr-2 text-[12px] text-white/80">
              {events.length === 0 ? (
                <p className="text-primary-fixed-dim">Waiting for pipeline events…</p>
              ) : (
                events.slice(-8).map((event, index) => (
                  <p key={`${event.timestamp}-${index}`}>
                    {event.type}: {event.message}
                  </p>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
