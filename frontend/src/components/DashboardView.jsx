export default function DashboardView({ runs, onNewApplication, onOpenRun }) {
  const completed = runs.filter((run) => run.status === "completed").length;
  const total = runs.length;
  const failed = runs.filter((run) => run.status === "failed").length;

  return (
    <div className="space-y-10">
      <section className="relative overflow-hidden border-b-4 border-primary-light bg-primary p-12 text-white shadow-institutional-lg">
        <div className="absolute right-0 top-0 p-4 opacity-10">
          <span className="material-symbols-outlined text-[160px]">corporate_fare</span>
        </div>
        <div className="relative z-10">
          <div className="mb-8 inline-flex items-center gap-2 border border-white/20 bg-white/10 px-3 py-1">
            <span className="material-symbols-outlined text-[16px]">verified_user</span>
            <span className="font-mono text-[12px] font-bold uppercase tracking-[0.2em]">
              SYSTEM.TERMINAL.ACTIVE
            </span>
          </div>
          <h2 className="mb-4 text-[48px] font-extrabold uppercase leading-none tracking-tighter">
            CareerPilot Intelligence
          </h2>
          <p className="max-w-lg border-l-2 border-white/30 pl-6 text-[18px] italic leading-relaxed text-primary-fixed-dim">
            Research. Personalize. Verify.
            <br />
            <span className="font-bold not-italic text-white">
              Engineered for maximum application yield.
            </span>
          </p>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Applications.Total", value: total, icon: "trending_up", badge: "Live" },
          { label: "Completed.Runs", value: completed, icon: "psychology", badge: "Ready" },
          { label: "Failed.Runs", value: failed, icon: "rule", badge: "Audit" },
          { label: "Pipeline.Agents", value: 2, icon: "hub", badge: "Active" },
        ].map((stat) => (
          <div
            key={stat.label}
            className="institutional-panel p-6 transition-all hover:border-primary"
          >
            <div className="mb-4 flex items-start justify-between">
              <div className="flex h-10 w-10 items-center justify-center bg-primary text-white">
                <span className="material-symbols-outlined">{stat.icon}</span>
              </div>
              <span className="bg-primary-fixed px-2 py-0.5 text-[10px] font-bold text-primary">
                {stat.badge}
              </span>
            </div>
            <p className="label-caps mb-1">{stat.label}</p>
            <h3 className="font-mono text-[32px] font-black text-primary">{stat.value}</h3>
          </div>
        ))}
      </section>

      <section className="institutional-border border-2 border-primary shadow-institutional-lg">
        <div className="flex items-center justify-between border-b border-primary bg-surface p-8">
          <div>
            <h3 className="text-[20px] font-black uppercase tracking-tight text-primary">
              Registry of Applications
            </h3>
            <p className="text-[13px] font-medium text-on-surface-variant">
              Systematic tracking of generated application materials.
            </p>
          </div>
          <button type="button" className="btn-primary" onClick={onNewApplication}>
            New Application
            <span className="material-symbols-outlined text-[18px]">add</span>
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-primary font-mono text-left text-white">
                {["Entity", "Status.Flag", "Created", "Ops"].map((header, index, arr) => (
                  <th
                    key={header}
                    className={`px-8 py-4 text-[11px] font-bold uppercase tracking-widest ${
                      index < arr.length - 1 ? "border-r border-white/10" : "text-right"
                    }`}
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant bg-white">
              {runs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-8 py-10 text-center text-on-surface-variant">
                    No applications yet. Start your first run.
                  </td>
                </tr>
              ) : (
                runs.map((run) => (
                  <tr key={run.id} className="transition-colors hover:bg-surface-container-low">
                    <td className="border-r border-outline-variant/30 px-8 py-5">
                      <span className="font-bold uppercase tracking-tight text-on-surface">
                        {run.companyName}
                      </span>
                    </td>
                    <td className="border-r border-outline-variant/30 px-8 py-5">
                      <span
                        className={
                          run.status === "completed"
                            ? "status-ready"
                            : run.status === "failed"
                              ? "status-failed"
                              : "status-running"
                        }
                      >
                        {run.status}
                      </span>
                    </td>
                    <td className="border-r border-outline-variant/30 px-8 py-5 font-mono text-[13px]">
                      {new Date(run.createdAt).toLocaleString()}
                    </td>
                    <td className="px-8 py-5 text-right">
                      <button
                        type="button"
                        className="text-on-surface-variant hover:text-primary"
                        onClick={() => onOpenRun(run)}
                      >
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
