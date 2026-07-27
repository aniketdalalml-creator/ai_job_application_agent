const WORKFLOW_STEPS = [
  { id: "research", label: "Company Research", detail: "WEB_SEARCH + STRUCTURED_HANDOFF" },
  { id: "handoff", label: "Structured Handoff", detail: "JSON_STATE_READY" },
  { id: "draft", label: "Draft Materials", detail: "COVER_LETTER + RESUME_BULLETS" },
  { id: "critique", label: "Self Critique", detail: "CLAIM_VERIFICATION" },
  { id: "revise", label: "Revision Pass", detail: "CONDITIONAL_OPTIMIZATION" },
  { id: "complete", label: "Final Output", detail: "PACKAGE_READY" },
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
    complete: runStatus === "completed",
  };

  const firstIncomplete = order.find((id) => !completed[id]);
  if (completed[stepId]) return "done";
  if (firstIncomplete === stepId) return "active";
  return "pending";
}

function progressPercent(events, runStatus) {
  const states = WORKFLOW_STEPS.map((step) => stepState(step.id, events, runStatus));
  const doneCount = states.filter((state) => state === "done").length;
  if (runStatus === "completed") return 100;
  return Math.min(99, Math.round((doneCount / WORKFLOW_STEPS.length) * 100));
}

export default function ProcessingView({ companyName, events, runStatus }) {
  const progress = progressPercent(events, runStatus);
  const activeStep = WORKFLOW_STEPS.find((step) => stepState(step.id, events, runStatus) === "active");

  return (
    <div className="mx-auto max-w-content space-y-10">
      <div className="flex flex-col justify-between gap-8 pt-4 lg:flex-row lg:items-end">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 border border-primary/20 bg-primary/10 px-2 py-0.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
            </span>
            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
              Active Analysis
            </span>
          </div>
          <h2 className="max-w-2xl text-[36px] font-semibold leading-[1.1] tracking-tight">
            Orchestrating application materials for{" "}
            <span className="border-b-4 border-primary/20 uppercase">{companyName}</span>
          </h2>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
        <div className="lg:col-span-5">
          <div className="institutional-panel h-full p-6">
            <div className="mb-8 flex items-center justify-between border-b border-outline-variant/30 pb-4">
              <h3 className="text-[13px] font-bold uppercase tracking-[0.15em] text-primary">
                Agent Workflow
              </h3>
              <span className="text-[11px] font-bold text-on-surface-variant">
                {runStatus?.toUpperCase()}
              </span>
            </div>

            <div className="relative space-y-6">
              <div className="absolute bottom-2 left-[13px] top-2 w-px bg-outline-variant" />
              {WORKFLOW_STEPS.map((step) => {
                const state = stepState(step.id, events, runStatus);
                return (
                  <div key={step.id} className={`relative flex items-start gap-4 ${state === "pending" ? "opacity-40" : ""}`}>
                    <div
                      className={`z-10 flex h-[27px] w-[27px] items-center justify-center rounded-sm ${
                        state === "done"
                          ? "bg-primary text-white"
                          : state === "active"
                            ? "border border-primary bg-white text-primary"
                            : "border border-outline-variant bg-surface-container text-secondary"
                      }`}
                    >
                      {state === "done" ? (
                        <span className="material-symbols-outlined text-[14px] font-bold">check</span>
                      ) : state === "active" ? (
                        <div className="h-1.5 w-1.5 animate-pulse bg-primary" />
                      ) : (
                        <span className="material-symbols-outlined text-[14px]">more_horiz</span>
                      )}
                    </div>
                    <div className="flex-1 pt-1">
                      <p
                        className={`text-[13px] font-bold uppercase tracking-tight ${
                          state === "active" ? "text-primary" : "text-on-surface"
                        }`}
                      >
                        {step.label}
                      </p>
                      <p className="mt-0.5 font-mono text-[11px] text-secondary">{step.detail}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-4 lg:col-span-7">
          <div className="institutional-panel flex flex-1 flex-col items-center justify-center p-10 text-center">
            <div className="relative mb-8">
              <div className="relative z-10 flex h-44 w-44 items-center justify-center border border-outline-variant bg-white shadow-sm">
                <div className="text-center">
                  <span className="text-[44px] font-semibold text-primary">{progress}</span>
                  <span className="text-[16px] font-bold tracking-widest text-secondary">%</span>
                </div>
              </div>
            </div>
            <div className="w-full max-w-sm space-y-6">
              <div className="space-y-2">
                <h4 className="text-[18px] font-bold uppercase tracking-[0.1em] text-primary">
                  Compiling Trajectory
                </h4>
                <p className="text-[13px] leading-relaxed text-secondary">
                  {activeStep
                    ? `Executing ${activeStep.label.toLowerCase()} for ${companyName}.`
                    : "Finalizing application package."}
                </p>
              </div>
              <div className="relative h-2 w-full border border-outline-variant/30 bg-surface-container-high">
                <div
                  className="absolute left-0 top-0 h-full bg-primary transition-all duration-700"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          </div>

          <div className="flex h-48 flex-col overflow-hidden bg-console p-5 shadow-lg">
            <div className="mb-3 flex items-center justify-between border-b border-white/10 pb-2">
              <span className="font-mono text-[10px] uppercase tracking-[0.2em] text-white/50">
                INSTITUTIONAL_CONSOLE
              </span>
            </div>
            <div className="space-y-1.5 overflow-y-auto pr-2 font-mono text-[11px] text-white/80">
              {events.length === 0 ? (
                <p className="text-blue-300">&gt; WAITING: pipeline events...</p>
              ) : (
                events.slice(-8).map((event, index) => (
                  <p key={`${event.timestamp}-${index}`} className="text-blue-200">
                    &gt; {event.type.toUpperCase()}: {event.message}
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
