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

export default function ResultsView({
  companyName,
  handoff,
  finalMaterials,
  critique,
  revised,
  fit,
  error,
}) {
  const bulletCount = finalMaterials?.resumeBullets?.length || 0;
  const factCount = handoff?.companyFacts?.length || 0;
  const scored = fit && fit.overall_score != null;
  const score = scored ? Math.round(fit.overall_score) : null;

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-16">
      {error ? (
        <div className="rounded-2xl border border-error/30 bg-error-container px-4 py-3 text-[13px] font-medium text-error">
          {error}
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        <div className="institutional-panel flex flex-col items-center p-8 text-center lg:col-span-5">
          <div className="relative mb-6 h-44 w-44">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" fill="transparent" stroke="#eaedff" strokeWidth="8" />
              {scored ? (
                <circle
                  cx="50"
                  cy="50"
                  r="42"
                  fill="transparent"
                  stroke="#0058be"
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray="264"
                  strokeDashoffset={264 - (264 * score) / 100}
                />
              ) : null}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[40px] font-bold tracking-tight">{scored ? `${score}%` : "—"}</span>
              <span className="text-[11px] font-semibold uppercase tracking-wider text-on-surface-variant">
                {scored ? fit.recommendation || "Fit score" : "Unscored"}
              </span>
            </div>
          </div>
          <h2 className="mb-2 text-[18px] font-semibold">{companyName}</h2>
          <p className="text-[13px] leading-relaxed text-on-surface-variant">
            {scored
              ? fit.reasoning || "Fit scored from your profile against this role."
              : "Materials cross-referenced against your resume and company research."}
          </p>
          {scored ? (
            <div className="mt-6 w-full space-y-3 text-left">
              <ScoreBar label="Skills" value={fit.skill_match_score} />
              <ScoreBar label="Experience" value={fit.experience_match_score} />
              <ScoreBar label="Role" value={fit.role_match_score} />
            </div>
          ) : null}
        </div>

        <div className="grid grid-cols-2 gap-3 lg:col-span-7">
          {[
            { icon: "verified_user", label: "Company facts", value: `${factCount} sourced` },
            { icon: "format_list_bulleted", label: "Resume bullets", value: `${bulletCount} tailored` },
            { icon: "rule", label: "Critique", value: critique?.hasIssues ? "Revised" : "Passed" },
            { icon: "assignment_turned_in", label: "Revision", value: revised ? "Applied" : "Skipped" },
          ].map((item) => (
            <div key={item.label} className="institutional-panel p-5">
              <span className="material-symbols-outlined mb-3 block text-[22px] text-primary">{item.icon}</span>
              <p className="label-caps mb-1">{item.label}</p>
              <p className="text-[18px] font-semibold">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      {scored && (fit.strengths?.length || fit.gaps?.length) ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div className="institutional-panel p-6">
            <p className="text-[14px] font-semibold text-match">Strengths</p>
            <ul className="mt-3 space-y-2">
              {(fit.strengths || []).map((item) => (
                <li key={item} className="rounded-xl bg-match-soft px-3 py-2 text-[13px] leading-relaxed">
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="institutional-panel p-6">
            <p className="text-[14px] font-semibold text-warning">Gaps</p>
            <ul className="mt-3 space-y-2">
              {(fit.gaps || []).map((item) => (
                <li key={item} className="rounded-xl bg-warning-soft px-3 py-2 text-[13px] leading-relaxed text-warning">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="institutional-panel p-6">
          <p className="text-[14px] font-semibold">Cover letter</p>
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap rounded-xl bg-surface-container-low p-4 text-[13px] leading-relaxed">
            {finalMaterials?.coverLetter || "No cover letter generated."}
          </pre>
        </div>
        <div className="institutional-panel p-6">
          <p className="text-[14px] font-semibold">Tailored resume bullets</p>
          <ul className="mt-3 space-y-2">
            {(finalMaterials?.resumeBullets || []).map((bullet) => (
              <li key={bullet} className="rounded-xl bg-surface-container-low px-3 py-2 text-[13px] leading-relaxed">
                {bullet}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {handoff ? (
        <div className="institutional-panel p-6">
          <p className="mb-3 text-[14px] font-semibold">Research handoff</p>
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-surface-container-low p-4 font-mono text-[12px]">
            {JSON.stringify(handoff, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
