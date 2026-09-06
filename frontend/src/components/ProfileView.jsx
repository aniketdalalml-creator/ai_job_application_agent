function csvToList(value) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function fieldTone(field, interview) {
  if (!interview) return "";
  if ((interview.inferred_fields || []).includes(field)) return "inferred";
  if ((interview.resolved_fields || []).includes(field)) return "confirmed";
  if (interview.question_field === field) return "review";
  const confidence = interview.confidence?.[field];
  if (confidence != null && confidence < 0.65) return "review";
  return "";
}

function FieldLabel({ children, tone }) {
  return (
    <span className="label-caps">
      {children}
      {tone === "review" ? <span className="field-badge-review">Needs review</span> : null}
      {tone === "inferred" ? <span className="field-badge-inferred">Inferred</span> : null}
      {tone === "confirmed" ? <span className="field-badge-confirmed">Confirmed</span> : null}
    </span>
  );
}

export default function ProfileView({
  profile,
  setProfile,
  interview,
  saving,
  uploading,
  error,
  success,
  onSave,
  onUpload,
  onFieldEdit,
}) {
  function update(field, value) {
    setProfile((current) => ({ ...current, [field]: value }));
    onFieldEdit?.(field);
  }

  return (
    <div className="mx-auto max-w-4xl space-y-10">
      <div className="space-y-3">
        <p className="label-caps text-primary">Profile</p>
        <h2 className="text-[36px] font-bold leading-tight tracking-tight">
          Tell the agent who you are looking for
        </h2>
      </div>
      <form onSubmit={onSave} className="institutional-panel space-y-6 p-8">
        <label className="block space-y-2">
          <FieldLabel tone={fieldTone("target_titles", interview)}>Target titles (comma separated)</FieldLabel>
          <input
            className="input-field"
            value={(profile.target_titles || []).join(", ")}
            onChange={(event) => update("target_titles", csvToList(event.target.value))}
            placeholder="Machine Learning Engineer, AI Engineer"
          />
        </label>
        <label className="block space-y-2">
          <FieldLabel tone={fieldTone("skills", interview)}>Skills (comma separated)</FieldLabel>
          <input
            className="input-field"
            value={(profile.skills || []).join(", ")}
            onChange={(event) => update("skills", csvToList(event.target.value))}
            placeholder="Python, FastAPI, RAG, PyTorch"
          />
        </label>
        <div className="grid gap-6 md:grid-cols-2">
          <label className="block space-y-2">
            <FieldLabel tone={fieldTone("years_experience", interview)}>Years of experience</FieldLabel>
            <input
              className="input-field"
              type="number"
              min="0"
              step="0.5"
              value={profile.years_experience ?? 0}
              onChange={(event) => update("years_experience", Number(event.target.value))}
            />
          </label>
          <label className="block space-y-2">
            <FieldLabel tone={fieldTone("work_mode", interview)}>Work mode</FieldLabel>
            <select
              className="input-field"
              value={profile.work_mode || "hybrid"}
              onChange={(event) => update("work_mode", event.target.value)}
            >
              <option value="hybrid">Hybrid</option>
              <option value="remote">Remote</option>
              <option value="on-site">On-site</option>
            </select>
          </label>
          <label className="block space-y-2">
            <FieldLabel tone={fieldTone("locations", interview)}>Locations (comma separated)</FieldLabel>
            <input
              className="input-field"
              value={(profile.locations || []).join(", ")}
              onChange={(event) => update("locations", csvToList(event.target.value))}
              placeholder="Bengaluru, Remote"
            />
          </label>
          <label className="block space-y-2">
            <FieldLabel tone={fieldTone("country", interview)}>Adzuna country code</FieldLabel>
            <input
              className="input-field"
              value={profile.country || "us"}
              onChange={(event) => update("country", event.target.value)}
              placeholder="us, in, gb"
              maxLength={2}
            />
          </label>
        </div>
        <div className="space-y-3 rounded-2xl bg-surface-container-low p-4">
          <div>
            <p className="label-caps">Upload resume</p>
            <p className="mt-1 text-[13px] text-on-surface-variant">
              PDF, DOCX, or TXT. We draft titles and skills, then Copilot asks about anything unclear.
            </p>
          </div>
          <label className="btn-secondary inline-flex cursor-pointer">
            <span className="material-symbols-outlined text-[18px]">upload_file</span>
            {uploading ? "Reading resume..." : "Choose file"}
            <input
              type="file"
              accept=".pdf,.txt,.docx,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              className="hidden"
              disabled={uploading || saving}
              onChange={(event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (file) onUpload(file);
              }}
            />
          </label>
        </div>
        <label className="block space-y-2">
          <span className="label-caps">Resume</span>
          <textarea
            className="input-field min-h-[220px] resize-y font-mono text-[12px]"
            value={profile.resume_text || ""}
            onChange={(event) => update("resume_text", event.target.value)}
            placeholder="Paste your resume text"
          />
        </label>
        {error ? <p className="text-[13px] font-medium text-error">{error}</p> : null}
        {success ? <p className="text-[13px] font-medium text-primary">{success}</p> : null}
        <button type="submit" className="btn-primary" disabled={saving}>
          {saving ? "Saving..." : "Save profile"}
        </button>
      </form>
    </div>
  );
}
