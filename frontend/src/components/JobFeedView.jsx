function matchBadge(fit) {
  if (!fit || fit.overall_score == null) {
    return { label: "Unscored", className: "bg-surface-container text-on-surface-variant" };
  }
  const score = Math.round(fit.overall_score);
  if (fit.recommendation === "APPLY") {
    return { label: `${score}% match`, className: "bg-emerald-500 text-white" };
  }
  if (fit.recommendation === "SKIP") {
    return { label: `${score}% match`, className: "bg-error-container text-error" };
  }
  return { label: `${score}% match`, className: "bg-warning-soft text-warning" };
}

function ScoreBar({ label, value }) {
  const score = Math.round(value ?? 0);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px] text-on-surface-variant">
        <span>{label}</span>
        <span>{score}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-surface-container">
        <div className="h-full rounded-full bg-primary" style={{ width: `${Math.min(100, Math.max(0, score))}%` }} />
      </div>
    </div>
  );
}

export default function JobFeedView({
  jobs,
  filter,
  setFilter,
  searching,
  error,
  hasResume,
  onSearch,
  onPrepare,
}) {
  return (
    <div className="relative space-y-6">
      <div className="pointer-events-none absolute right-1/4 top-0 h-96 w-96 rounded-full bg-primary/5 blur-3xl" />

      <div className="relative flex flex-wrap items-end justify-between gap-4">
        <div className="max-w-2xl">
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-full bg-surface-container px-2.5 py-0.5">
            <span className="material-symbols-outlined text-[14px] text-secondary-container">auto_awesome</span>
            <span className="text-[11px] font-semibold uppercase tracking-wider text-secondary-container">
              Ranked from your profile
            </span>
          </div>
          <h2 className="text-[36px] font-bold leading-tight tracking-tight">Job matches</h2>
          <p className="mt-1 text-[15px] text-on-surface-variant">
            Search uses your saved profile. Each posting is scored APPLY / MAYBE / SKIP before you prepare materials.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={onSearch} disabled={searching}>
          <span className="material-symbols-outlined text-[18px]">travel_explore</span>
          {searching ? "Searching..." : "Find jobs"}
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {["ALL", "APPLY", "MAYBE", "SKIP"].map((item) => (
          <button
            key={item}
            type="button"
            className={filter === item ? "btn-primary !py-1.5 !text-[12px]" : "btn-secondary !py-1.5 !text-[12px]"}
            onClick={() => setFilter(item)}
          >
            {item}
          </button>
        ))}
      </div>

      {error ? <p className="text-[13px] font-medium text-error">{error}</p> : null}
      {!hasResume ? (
        <p className="text-[13px] text-on-surface-variant">Add a resume on your Profile before preparing an application.</p>
      ) : null}

      <div className="grid gap-4">
        {jobs.length === 0 ? (
          <div className="institutional-panel p-10 text-center text-on-surface-variant">
            No jobs yet. Save a profile, then run Find jobs.
          </div>
        ) : (
          jobs.map((job) => {
            const fit = job.fit;
            const scored = fit && fit.overall_score != null;
            const badge = matchBadge(fit);
            return (
              <article key={job.id} className="institutional-panel relative p-5">
                <span
                  className={`absolute -top-2.5 right-5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold shadow-sm ${badge.className}`}
                >
                  {badge.label}
                </span>
                <div className="grid gap-5 lg:grid-cols-12">
                  <div className="flex items-start gap-3 lg:col-span-8">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-surface-container text-primary">
                      <span className="material-symbols-outlined">domain</span>
                    </div>
                    <div className="min-w-0 flex-1 space-y-2">
                      <div>
                        <p className="text-[12px] font-bold text-primary">
                          {job.company} · <span className="font-medium text-outline">{job.location || "Location n/a"}</span>
                        </p>
                        <h3 className="text-[18px] font-semibold tracking-tight">{job.title || "Pasted role"}</h3>
                      </div>
                      <p className="line-clamp-3 text-[13px] leading-relaxed text-on-surface-variant">{job.description}</p>
                      {scored ? (
                        <div className="grid gap-2 sm:grid-cols-3">
                          <ScoreBar label="Skills" value={fit.skill_match_score} />
                          <ScoreBar label="Experience" value={fit.experience_match_score} />
                          <ScoreBar label="Role" value={fit.role_match_score} />
                        </div>
                      ) : null}
                      {fit?.strengths?.length ? (
                        <p className="text-[12px] text-on-surface">Strengths: {fit.strengths.slice(0, 3).join(" · ")}</p>
                      ) : null}
                      {fit?.gaps?.length ? (
                        <p className="text-[12px] text-error">Gaps: {fit.gaps.slice(0, 3).join(" · ")}</p>
                      ) : null}
                    </div>
                  </div>
                  <div className="flex flex-col justify-center gap-2 lg:col-span-4">
                    {job.application_status ? (
                      <span className="status-completed text-center">{job.application_status}</span>
                    ) : null}
                    <button
                      type="button"
                      className="btn-primary w-full"
                      onClick={() => onPrepare(job)}
                      disabled={!hasResume}
                      title={hasResume ? "Prepare application" : "Add a resume on your Profile first"}
                    >
                      Prepare application
                    </button>
                    {job.url ? (
                      <a className="btn-secondary w-full" href={job.url} target="_blank" rel="noreferrer">
                        Open posting
                      </a>
                    ) : null}
                  </div>
                </div>
              </article>
            );
          })
        )}
      </div>
    </div>
  );
}
