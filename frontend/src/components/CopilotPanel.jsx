function eventTone(type) {
  if (type.includes("error")) return "text-error";
  if (type.includes("complete") || type === "handoff") return "text-emerald-700";
  if (type.includes("tool")) return "text-amber-700";
  return "text-secondary";
}

export default function CopilotPanel({
  companyName,
  events,
  runStatus,
  finalMaterials,
  critique,
  onQuickAction,
}) {
  const latestEvent = events[events.length - 1];
  const isRunning = runStatus === "running" || runStatus === "queued";

  return (
    <aside className="fixed right-0 top-0 z-50 flex h-full w-96 flex-col border-l-2 border-primary bg-white">
      <div className="border-b-2 border-primary bg-primary p-8 text-white">
        <div className="mb-2 flex items-center gap-3">
          <span className="material-symbols-outlined font-bold">memory</span>
          <h2 className="text-[18px] font-black uppercase tracking-widest">Copilot Core</h2>
        </div>
        <p className="text-[11px] font-bold uppercase tracking-wider text-primary-fixed-dim">
          {isRunning ? "Strategic Analysis Engine Active" : "Awaiting next command"}
        </p>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto bg-surface-container-low p-6 font-mono text-[13px]">
        {!events.length ? (
          <div className="institutional-panel relative p-5 leading-relaxed text-on-surface">
            <p>
              [SYSTEM] Hello. Submit a new application to begin company research, structured handoff,
              and tailored document generation.
            </p>
          </div>
        ) : (
          events.map((event, index) => (
            <div
              key={`${event.timestamp}-${index}`}
              className="institutional-panel relative p-4 leading-relaxed"
            >
              <p className={`label-caps mb-1 ${eventTone(event.type)}`}>
                {event.agent || "pipeline"} · {event.type}
              </p>
              <p className="text-[12px] text-on-surface">{event.message}</p>
              <p className="mt-2 text-[10px] text-on-surface-variant">
                {new Date(event.timestamp).toLocaleTimeString()}
              </p>
            </div>
          ))
        )}

        {finalMaterials ? (
          <div className="border-l-4 border-primary bg-white p-5 institutional-border">
            <span className="label-caps mb-2 block text-primary">Output Ready</span>
            <p className="text-[13px] leading-relaxed text-on-surface">
              Cover letter and resume bullets generated for <strong>{companyName}</strong>.
              {critique?.hasIssues ? " Materials were revised after critique." : " Draft passed critique."}
            </p>
          </div>
        ) : null}
      </div>

      <div className="space-y-6 border-t bg-white p-8">
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-secondary !px-4 !py-2 !text-[10px]" onClick={onQuickAction}>
            New Run
          </button>
          {latestEvent ? (
            <span className="status-running">{runStatus || "active"}</span>
          ) : null}
        </div>
        <div className="relative">
          <input
            className="input-field !py-4 pl-5 pr-14 font-mono !text-[12px]"
            placeholder="Enter command or query..."
            disabled
          />
          <button
            type="button"
            className="absolute right-3 top-3 bg-primary p-2 text-white"
            disabled
          >
            <span className="material-symbols-outlined text-[18px]">keyboard_return</span>
          </button>
        </div>
      </div>
    </aside>
  );
}
