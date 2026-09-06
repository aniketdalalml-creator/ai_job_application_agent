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

export default function ApplicationsView({ applications, onOpen, onStatus }) {
  return (
    <div className="space-y-6">
      <div>
        <p className="label-caps text-primary">Tracker</p>
        <h2 className="mt-1 text-[32px] font-bold tracking-tight">Applications</h2>
      </div>
      <section className="institutional-panel overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-surface-container text-left text-on-surface-variant">
                {["Company", "Role", "Status", "Updated", ""].map((header) => (
                  <th key={header || "ops"} className="px-6 py-3 text-[12px] font-semibold">
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/60">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-8 py-10 text-center text-on-surface-variant">
                    No applications yet. Prepare one from Job Matches.
                  </td>
                </tr>
              ) : (
                applications.map((item) => (
                  <tr key={item.id} className="hover:bg-surface-container-low">
                    <td className="px-6 py-4 font-semibold">{item.company}</td>
                    <td className="px-6 py-4 text-[13px] text-on-surface-variant">{item.title}</td>
                    <td className="px-6 py-4">
                      <select
                        className="input-field !py-2"
                        value={item.status}
                        onChange={(event) => onStatus(item.id, event.target.value)}
                      >
                        {STATUSES.map((status) => (
                          <option key={status} value={status}>
                            {status}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-6 py-4 text-[12px] text-outline">
                      {item.updated_at ? new Date(item.updated_at).toLocaleString() : "—"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button type="button" className="rounded-full p-2 text-primary hover:bg-primary-fixed" onClick={() => onOpen(item)}>
                        <span className="material-symbols-outlined">open_in_new</span>
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
