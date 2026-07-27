export default function NewApplicationView({
  companyName,
  setCompanyName,
  jobDescription,
  setJobDescription,
  resumeText,
  setResumeText,
  submitting,
  error,
  onSubmit,
}) {
  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <div className="space-y-4 pt-4">
        <div className="inline-flex items-center gap-2 border border-primary/20 bg-primary/10 px-2 py-0.5">
          <span className="relative flex h-1.5 w-1.5">
            <span className="absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-primary" />
          </span>
          <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-primary">
            New Application Entry
          </span>
        </div>
        <h2 className="max-w-2xl text-[36px] font-semibold leading-[1.1] tracking-tight text-on-surface">
          Configure your next application with{" "}
          <span className="border-b-4 border-primary/20">institutional precision</span>.
        </h2>
      </div>

      <form onSubmit={onSubmit} className="institutional-panel space-y-6 p-8">
        <div className="border-b border-outline-variant/30 pb-4">
          <h3 className="text-[13px] font-bold uppercase tracking-[0.15em] text-primary">
            Application Parameters
          </h3>
        </div>

        <label className="block space-y-2">
          <span className="label-caps">Target Entity</span>
          <input
            className="input-field"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            placeholder="Company name"
            required
          />
        </label>

        <label className="block space-y-2">
          <span className="label-caps">Position Specification</span>
          <textarea
            className="input-field min-h-[180px] resize-y font-mono text-[12px]"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            required
          />
        </label>

        <label className="block space-y-2">
          <span className="label-caps">Candidate Resume</span>
          <textarea
            className="input-field min-h-[180px] resize-y font-mono text-[12px]"
            value={resumeText}
            onChange={(event) => setResumeText(event.target.value)}
            required
          />
        </label>

        {error ? <p className="text-[13px] font-medium text-error">{error}</p> : null}

        <div className="flex items-center gap-4 pt-2">
          <button type="submit" className="btn-primary" disabled={submitting}>
            <span className="material-symbols-outlined text-[18px]">bolt</span>
            {submitting ? "Queueing..." : "Execute Pipeline"}
          </button>
        </div>
      </form>
    </div>
  );
}
