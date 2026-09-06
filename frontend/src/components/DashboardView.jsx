function statusClass(status) {
  if (status === "failed") return "status-failed";
  if (status === "generating") return "status-running";
  if (status === "ready" || status === "applied" || status === "offer") return "status-ready";
  return "status-completed";
}

export default function DashboardView({
  user,
  profile,
  insights,
  applications,
  onNewApplication,
  onOpenApplication,
  onFindJobs,
}) {
  const firstName = (user?.name || "there").split(" ")[0];
  const titles = (profile?.target_titles || []).slice(0, 2).join(" / ") || "your target roles";
  const locations = (profile?.locations || []).slice(0, 2).join(" & ") || "your locations";
  const applyCount = insights?.by_recommendation?.APPLY ?? 0;
  const suggestion = insights?.suggestions?.[0];

  const stats = [
    {
      label: "Job matches",
      value: insights?.jobs_found ?? 0,
      icon: "radar",
      tone: "bg-tertiary-fixed text-tertiary",
      hint: applyCount ? `${applyCount} APPLY tier` : "Run a search",
    },
    {
      label: "Average fit",
      value: Math.round(insights?.avg_fit ?? 0),
      icon: "psychology",
      tone: "bg-primary-fixed text-primary",
      hint: "Across scored roles",
    },
    {
      label: "Applications",
      value: insights?.application_count ?? 0,
      icon: "rocket_launch",
      tone: "bg-secondary-fixed text-secondary",
      hint: "Prepared and tracked",
    },
    {
      label: "APPLY tier",
      value: applyCount,
      icon: "verified",
      tone: "bg-surface-container-high text-on-surface",
      hint: "Strongest matches",
    },
  ];

  return (
    <div className="relative space-y-8">
      <div className="pointer-events-none absolute -top-24 left-1/4 h-96 w-96 rounded-full bg-primary-fixed/20 blur-3xl" />
      <div className="pointer-events-none absolute right-10 top-32 h-80 w-80 rounded-full bg-tertiary-fixed/30 blur-3xl" />

      <section className="relative flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 rounded-full bg-surface-container-highest px-3 py-1 text-[12px] font-semibold text-secondary shadow-sm">
            <span className="h-2 w-2 animate-pulse rounded-full bg-secondary-container" />
            Live workspace
          </div>
          <h2 className="text-[36px] font-bold leading-tight tracking-tight">Welcome back, {firstName}</h2>
          <p className="flex flex-wrap items-center gap-2 text-[15px] text-on-surface-variant">
            <span>Targeting</span>
            <span className="font-semibold text-primary">{titles}</span>
            <span className="text-outline">/</span>
            <span>{profile?.years_experience ? `${profile.years_experience} yrs` : "Experience unset"}</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-surface-container px-2 py-0.5 text-[12px]">
              <span className="material-symbols-outlined text-[14px] text-primary">pin_drop</span>
              {locations}
            </span>
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn-secondary" onClick={onNewApplication}>
            Paste a job
          </button>
          <button type="button" className="btn-primary" onClick={onFindJobs}>
            <span className="material-symbols-outlined text-[18px]">auto_awesome</span>
            Find jobs
          </button>
        </div>
      </section>

      <section className="relative grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <div key={stat.label} className="institutional-panel flex flex-col justify-between p-5">
            <div className="flex items-start justify-between">
              <span className="text-[12px] font-semibold uppercase tracking-wider text-on-surface-variant">
                {stat.label}
              </span>
              <span className={`flex h-7 w-7 items-center justify-center rounded-full ${stat.tone}`}>
                <span className="material-symbols-outlined text-[16px]">{stat.icon}</span>
              </span>
            </div>
            <p className="mt-3 text-[32px] font-bold tracking-tight">{stat.value}</p>
            <p className="mt-1 text-[12px] text-on-surface-variant">{stat.hint}</p>
          </div>
        ))}
      </section>

      {suggestion ? (
        <section className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-surface-container-low via-surface-container-lowest to-surface-container-high p-6 shadow-institutional-lg">
          <div className="pointer-events-none absolute -right-16 -top-16 h-64 w-64 rounded-full bg-tertiary/10 blur-2xl" />
          <div className="relative flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-tertiary text-on-tertiary shadow-glow">
              <span className="material-symbols-outlined">auto_awesome</span>
            </span>
            <div>
              <p className="text-[12px] font-bold uppercase tracking-wider text-tertiary">Strategy insight</p>
              <p className="mt-1 text-[14px] leading-relaxed text-on-surface">{suggestion}</p>
            </div>
          </div>
        </section>
      ) : null}

      <section className="institutional-panel overflow-hidden">
        <div className="flex items-center justify-between px-6 py-5">
          <div>
            <h3 className="text-[20px] font-semibold tracking-tight">Recent applications</h3>
            <p className="text-[13px] text-on-surface-variant">Open a run to review materials or update status.</p>
          </div>
        </div>
        <div className="divide-y divide-outline-variant/60">
          {(applications || []).slice(0, 6).length === 0 ? (
            <p className="px-6 py-10 text-center text-on-surface-variant">No applications yet.</p>
          ) : (
            applications.slice(0, 6).map((item) => (
              <button
                key={item.id}
                type="button"
                className="flex w-full items-center justify-between px-6 py-4 text-left hover:bg-surface-container-low"
                onClick={() => onOpenApplication(item)}
              >
                <div>
                  <p className="font-semibold">{item.company}</p>
                  <p className="text-[13px] text-on-surface-variant">{item.title || "Untitled role"}</p>
                </div>
                <span className={statusClass(item.status)}>{item.status}</span>
              </button>
            ))
          )}
        </div>
      </section>
    </div>
  );
}
