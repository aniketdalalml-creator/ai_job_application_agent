const STATUSES = [
  "saved",
  "generating",
  "ready",
  "failed",
  "applied",
  "interviewing",
  "offer",
  "rejected",
  "withdrawn",
];

const STATUS_LABELS = {
  saved: "Saved",
  generating: "Generating",
  ready: "Ready",
  failed: "Failed",
  applied: "Applied",
  interviewing: "Interviewing",
  offer: "Offer",
  rejected: "Rejected",
  withdrawn: "Withdrawn",
};

const SOURCE_LABELS = {
  muse: "The Muse",
  remotive: "Remotive",
  adzuna: "Adzuna",
  apify: "Apify",
  manual: "Pasted",
};

function statusClass(status) {
  if (status === "failed" || status === "rejected") return "status-failed";
  if (status === "generating") return "status-running";
  if (status === "ready" || status === "applied" || status === "offer") return "status-ready";
  return "status-completed";
}

function statusLabel(status) {
  return STATUS_LABELS[status] || status || "Unknown";
}

function sourceLabel(source) {
  return SOURCE_LABELS[source] || source || "—";
}

export default function ApplicationsView({ applications, onOpen, onStatus }) {
  return (
    <div className="space-y-6">
      <div>
        <p className="label-caps text-primary">Tracker</p>
        <h2 className="mt-1 text-[32px] font-bold tracking-tight">Applications</h2>
        <p className="mt-1 max-w-2xl text-[14px] text-on-surface-variant">
          Jobs you prepared from Job Matches. Update status as you apply, interview, or get an offer.
        </p>
      </div>
      <section className="institutional-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[720px] border-collapse">
            <thead>
              <tr className="bg-surface-container text-left text-on-surface-variant">
                {["Company", "Role", "Source", "Status", "Updated", ""].map((header) => (
                  <th key={header || "ops"} className="px-6 py-3 text-[12px] font-semibold">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/60">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-8 py-10 text-center text-on-surface-variant">
                    No applications yet. Open Job Matches and click Prepare application.
                  </td>
                </tr>
              ) : (
                applications.map((item) => {
                  const current = item.status || "saved";
                  const options = STATUSES.includes(current) ? STATUSES : [current, ...STATUSES];
                  return (
                    <tr key={item.id} className="hover:bg-surface-container-low">
                      <td className="px-6 py-4 font-semibold">{item.company}</td>
                      <td className="px-6 py-4 text-[13px] text-on-surface-variant">{item.title}</td>
                      <td className="px-6 py-4 text-[12px] text-on-surface-variant">{sourceLabel(item.source)}</td>
                      <td className="px-6 py-4">
                        <div className="flex min-w-[11rem] items-center gap-2">
                          <span className={statusClass(current)}>{statusLabel(current)}</span>
                          <select
                            className="min-w-[7.5rem] rounded-xl border border-outline-variant bg-white px-2 py-1.5 text-[12px] font-medium text-[#131b2e]"
                            value={current}
                            aria-label={`Status for ${item.company}`}
                            onChange={(event) => onStatus(item.id, event.target.value)}
                          >
                            {options.map((status) => (
                              <option key={status} value={status}>
                                {statusLabel(status)}
                              </option>
                            ))}
                          </select>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-[12px] text-outline">
                        {item.updated_at ? new Date(item.updated_at).toLocaleString() : "—"}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          type="button"
                          className="rounded-full p-2 text-primary hover:bg-primary-fixed"
                          title="Open materials"
                          onClick={() => onOpen(item)}
                        >
                          <span className="material-symbols-outlined">open_in_new</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
