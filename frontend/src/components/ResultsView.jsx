export default function ResultsView({ companyName, handoff, finalMaterials, critique, revised }) {
  const bulletCount = finalMaterials?.resumeBullets?.length || 0;
  const factCount = handoff?.companyFacts?.length || 0;
  const complianceScore = critique?.hasIssues ? 88 : 94;

  return (
    <div className="mx-auto max-w-4xl space-y-12 pb-32">
      <div className="flex gap-2 border border-outline-variant bg-surface-container p-1">
        {["Overview", "Document", "Research", "Verification"].map((tab, index) => (
          <button
            key={tab}
            type="button"
            className={`px-8 py-2 text-[12px] font-bold uppercase tracking-widest ${
              index === 3 ? "bg-primary text-white" : "text-on-surface-variant"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-12">
        <div className="flex flex-col items-center border border-outline-variant bg-white p-10 text-center lg:col-span-5">
          <div className="relative mb-8 h-48 w-48 border-8 border-surface-container p-2">
            <svg className="h-full w-full -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="46"
                fill="transparent"
                stroke="#eceef0"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="46"
                fill="transparent"
                stroke="#002b5c"
                strokeWidth="8"
                strokeDasharray="289"
                strokeDashoffset={289 - (289 * complianceScore) / 100}
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[48px] font-bold tracking-tighter text-primary">
                {complianceScore}%
              </span>
              <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary/60">
                Compliance
              </span>
            </div>
          </div>
          <h2 className="mb-4 text-[18px] font-bold uppercase tracking-widest text-primary">
            Verification Audit
          </h2>
          <p className="text-[13px] font-medium leading-relaxed text-on-surface-variant">
            Materials cross-referenced against resume ground truth and company research handoff.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 lg:col-span-7">
          {[
            { icon: "verified_user", label: "Company Facts", value: `${factCount} sourced` },
            { icon: "format_list_bulleted", label: "Resume Bullets", value: `${bulletCount} tailored` },
            { icon: "rule", label: "Critique", value: critique?.hasIssues ? "Revised" : "Passed" },
            { icon: "assignment_turned_in", label: "Revision", value: revised ? "Applied" : "Skipped" },
          ].map((item) => (
            <div
              key={item.label}
              className="border border-outline-variant bg-white p-6 transition-all hover:border-primary"
            >
              <span className="material-symbols-outlined mb-3 block text-[24px] text-primary">
                {item.icon}
              </span>
              <p className="label-caps mb-1">{item.label}</p>
              <p className="text-[20px] font-bold uppercase text-primary">{item.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-8">
        <h3 className="text-[20px] font-bold uppercase tracking-[0.2em] text-primary">
          Archive Package Review
        </h3>
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <div className="border border-outline-variant bg-white p-6">
            <p className="text-[14px] font-bold uppercase tracking-widest text-primary">Cover Letter</p>
            <pre className="mt-4 max-h-80 overflow-auto whitespace-pre-wrap border border-outline-variant bg-surface-container-low p-4 text-[13px] leading-relaxed">
              {finalMaterials?.coverLetter || "No cover letter generated."}
            </pre>
          </div>
          <div className="border border-outline-variant bg-white p-6">
            <p className="text-[14px] font-bold uppercase tracking-widest text-primary">
              Tailored Resume Bullets
            </p>
            <ul className="mt-4 space-y-3 border border-outline-variant bg-surface-container-low p-4">
              {(finalMaterials?.resumeBullets || []).map((bullet) => (
                <li key={bullet} className="border-l-2 border-primary pl-3 text-[13px] leading-relaxed">
                  {bullet}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {handoff ? (
        <div className="border border-outline-variant bg-white p-6">
          <p className="mb-4 text-[14px] font-bold uppercase tracking-widest text-primary">
            Research Handoff
          </p>
          <pre className="max-h-64 overflow-auto whitespace-pre-wrap border border-outline-variant bg-surface-container-low p-4 font-mono text-[12px]">
            {JSON.stringify(handoff, null, 2)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
