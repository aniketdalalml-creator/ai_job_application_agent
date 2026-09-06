import { useState } from "react";

function eventTone(type) {
  if (type.includes("error")) return "text-error";
  if (type.includes("complete") || type === "handoff") return "text-match";
  if (type.includes("tool") || type.includes("fit")) return "text-tertiary";
  return "text-secondary";
}

export default function CopilotPanel({
  companyName,
  events,
  runStatus,
  finalMaterials,
  critique,
  onQuickAction,
  mode = "pipeline",
  interview,
  interviewMessages = [],
  interviewBusy = false,
  onInterviewSend,
  onInterviewSkip,
  onInterviewConfirm,
}) {
  const [draft, setDraft] = useState("");
  const latestEvent = events[events.length - 1];
  const isRunning = runStatus === "running" || runStatus === "queued" || runStatus === "generating";
  const isProfile = mode === "profile";
  const canSkip = isProfile && Boolean(interview?.question) && !interview?.done;

  function submitChat(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || interviewBusy) return;
    setDraft("");
    onInterviewSend?.(text);
  }

  return (
    <aside className="fixed bottom-0 right-0 top-16 z-40 flex w-96 flex-col border-l border-outline-variant/60 bg-surface-container-lowest">
      <div className="border-b border-outline-variant/60 px-5 py-4">
        <div className="mb-1 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-tertiary text-on-tertiary shadow-glow">
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
          </span>
          <h2 className="text-[16px] font-semibold tracking-tight">Copilot</h2>
        </div>
        <p className="text-[12px] text-on-surface-variant">
          {isProfile
            ? "Clarify your search profile"
            : isRunning
              ? "Live pipeline events"
              : "Activity for your current run"}
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto bg-surface-container-low/60 p-4">
        {isProfile ? (
          <>
            {!interviewMessages.length ? (
              <div className="rounded-2xl border border-outline-variant/70 bg-surface-container-lowest p-4 text-[13px] leading-relaxed text-on-surface-variant">
                Upload a resume or tell me who you are looking for. I will ask about anything unclear, and
                guess if you skip.
              </div>
            ) : (
              interviewMessages.map((item, index) => (
                <div
                  key={`${item.role}-${index}`}
                  className="rounded-2xl border border-outline-variant/70 bg-surface-container-lowest p-4"
                >
                  <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-tertiary">
                    {item.role === "user" ? "You" : "Copilot"}
                  </p>
                  <p className="text-[13px] leading-relaxed text-on-surface">{item.content}</p>
                </div>
              ))
            )}
            {interviewBusy ? (
              <p className="text-[12px] text-on-surface-variant">Updating your profile...</p>
            ) : null}
          </>
        ) : (
          <>
            {!events.length ? (
              <div className="rounded-2xl border border-outline-variant/70 bg-surface-container-lowest p-4 text-[13px] leading-relaxed text-on-surface-variant">
                Paste a job or run Find jobs to start research, fit scoring, and tailored materials.
              </div>
            ) : (
              events.map((event, index) => (
                <div
                  key={`${event.timestamp}-${index}`}
                  className="rounded-2xl border border-outline-variant/70 bg-surface-container-lowest p-4"
                >
                  <p className={`mb-1 text-[11px] font-semibold uppercase tracking-wide ${eventTone(event.type)}`}>
                    {event.agent || "pipeline"} · {event.type}
                  </p>
                  <p className="text-[13px] text-on-surface">{event.message}</p>
                  <p className="mt-2 text-[11px] text-outline">
                    {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ""}
                  </p>
                </div>
              ))
            )}

            {finalMaterials ? (
              <div className="rounded-2xl border border-tertiary/20 bg-tertiary-fixed/40 p-4">
                <span className="mb-1 block text-[11px] font-semibold uppercase tracking-wide text-tertiary">
                  Materials ready
                </span>
                <p className="text-[13px] leading-relaxed text-on-surface">
                  Cover letter and resume bullets generated for <strong>{companyName}</strong>.
                  {critique?.hasIssues ? " Revised after critique." : " Draft passed critique."}
                </p>
              </div>
            ) : null}
          </>
        )}
      </div>

      <div className="space-y-3 border-t border-outline-variant/60 p-4">
        <div className="flex flex-wrap items-center gap-2">
          {isProfile ? (
            <>
              {canSkip ? (
                <button
                  type="button"
                  className="btn-secondary !px-4 !py-2 text-[12px]"
                  disabled={interviewBusy}
                  onClick={onInterviewSkip}
                >
                  Skip
                </button>
              ) : null}
              <button
                type="button"
                className="btn-secondary !px-4 !py-2 text-[12px]"
                disabled={interviewBusy}
                onClick={onInterviewConfirm}
              >
                Looks good — find jobs
              </button>
            </>
          ) : (
            <>
              <button type="button" className="btn-secondary !px-4 !py-2 text-[12px]" onClick={onQuickAction}>
                Paste a job
              </button>
              {latestEvent ? <span className="status-running">{runStatus || "active"}</span> : null}
            </>
          )}
        </div>
        <form className="relative" onSubmit={submitChat}>
          <input
            className="input-field !rounded-full !py-3 pl-5 pr-12 text-[13px]"
            placeholder={isProfile ? "Answer here, or skip and I will guess" : "Chat is not available yet"}
            disabled={!isProfile || interviewBusy}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
          <button
            type="submit"
            className="absolute right-1.5 top-1.5 rounded-full bg-surface-container p-2 text-outline disabled:opacity-40"
            disabled={!isProfile || interviewBusy || !draft.trim()}
          >
            <span className="material-symbols-outlined text-[18px]">send</span>
          </button>
        </form>
      </div>
    </aside>
  );
}
