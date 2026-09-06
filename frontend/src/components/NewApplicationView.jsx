export default function NewApplicationView({
  companyName,
  setCompanyName,
  jobTitle,
  setJobTitle,
  jobLocation,
  setJobLocation,
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
        <div className="inline-flex items-center gap-2 rounded-full bg-primary-fixed px-3 py-1 text-[12px] font-semibold text-primary">
          <span className="h-1.5 w-1.5 rounded-full bg-primary" />
          Paste a job
        </div>
        <h2 className="max-w-2xl text-[36px] font-bold leading-tight tracking-tight">
          Score a posting and generate tailored materials
        </h2>
      </div>

      <form onSubmit={onSubmit} className="institutional-panel space-y-6 p-8">
        <h3 className="text-[14px] font-semibold">Job details</h3>

        <label className="block space-y-2">
          <span className="label-caps">Company</span>
          <input
            className="input-field"
            value={companyName}
            onChange={(event) => setCompanyName(event.target.value)}
            placeholder="Company name"
            required
          />
        </label>

        <div className="grid gap-6 md:grid-cols-2">
          <label className="block space-y-2">
            <span className="label-caps">Role Title</span>
            <input
              className="input-field"
              value={jobTitle}
              onChange={(event) => setJobTitle(event.target.value)}
              placeholder="e.g. Senior Backend Engineer"
            />
          </label>
          <label className="block space-y-2">
            <span className="label-caps">Location</span>
            <input
              className="input-field"
              value={jobLocation}
              onChange={(event) => setJobLocation(event.target.value)}
              placeholder="e.g. Remote or Bengaluru"
            />
          </label>
        </div>

        <label className="block space-y-2">
          <span className="label-caps">Job description</span>
          <textarea
            className="input-field min-h-[180px] resize-y font-mono text-[12px]"
            value={jobDescription}
            onChange={(event) => setJobDescription(event.target.value)}
            required
          />
        </label>

        <label className="block space-y-2">
          <span className="label-caps">Resume</span>
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
            {submitting ? "Queueing..." : "Prepare application"}
          </button>
        </div>
      </form>
    </div>
  );
}
