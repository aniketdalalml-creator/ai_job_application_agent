import type { Job, JobFit } from "../types";

const SOURCE_LABELS: Record<string, { board: string; via: string }> = {
  muse: { board: "The Muse", via: "Public The Muse jobs API" },
  remotive: { board: "Remotive", via: "Public Remotive remote-jobs API" },
  adzuna: { board: "Adzuna", via: "Adzuna jobs API" },
  apify: { board: "Apify", via: "Apify job scraper (Indeed, LinkedIn)" },
  manual: { board: "Pasted job", via: "You pasted this listing" },
};

function sourceInfo(job: Job) {
  const key = (job.source || "").toLowerCase();
  const known = SOURCE_LABELS[key];
  if (known) return known;
  return { board: job.source || "Unknown", via: "Saved from an earlier search" };
}

function apifyBoard(externalId?: string) {
  const platform = (externalId || "").split(":")[0];
  if (!platform || platform === externalId) return "";
  return platform;
}

function formatSavedAt(value?: string | null) {
  if (!value) return "Not recorded";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function matchBadge(fit: JobFit | null | undefined) {
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

function ScoreBar({ label, value }: { label: string; value?: number }) {
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

type JobCardProps = {
  job: Job;
};

export default function JobCard({ job }: JobCardProps) {
  const fit = job.fit;
  const scored = Boolean(fit && fit.overall_score != null);
  const badge = matchBadge(fit);
  const origin = sourceInfo(job);
  const scrapedBoard = job.source === "apify" ? apifyBoard(job.external_id) : "";

  return (
    <article className="institutional-panel relative w-full min-w-0 p-5">
      <span className={`absolute -top-2.5 right-5 rounded-full px-2.5 py-0.5 text-[11px] font-semibold shadow-sm ${badge.className}`}>
        {badge.label}
      </span>
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-12">
        <div className="flex min-w-0 items-start gap-3 lg:col-span-8">
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
                <ScoreBar label="Skills" value={fit?.skill_match_score} />
                <ScoreBar label="Experience" value={fit?.experience_match_score} />
                <ScoreBar label="Role" value={fit?.role_match_score} />
              </div>
            ) : null}
            {fit?.strengths?.length ? (
              <p className="text-[12px] text-on-surface">Strengths: {fit.strengths.slice(0, 3).join(" · ")}</p>
            ) : null}
            {fit?.gaps?.length ? (
              <p className="text-[12px] text-error">Gaps: {fit.gaps.slice(0, 3).join(" · ")}</p>
            ) : null}
            <details className="rounded-xl border border-outline-variant/60 bg-surface-container-low/70 px-3 py-2">
              <summary className="cursor-pointer list-none text-[12px] font-semibold text-on-surface-variant [&::-webkit-details-marker]:hidden">
                <span className="inline-flex items-center gap-1.5">
                  <span className="material-symbols-outlined text-[16px]">info</span>
                  Source: {origin.board}
                  {scrapedBoard ? ` · ${scrapedBoard}` : ""}
                </span>
              </summary>
              <dl className="mt-2 grid gap-1.5 text-[12px] text-on-surface">
                <div className="flex justify-between gap-3">
                  <dt className="text-on-surface-variant">Board</dt>
                  <dd className="font-medium">{origin.board}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-on-surface-variant">Fetched via</dt>
                  <dd className="text-right">{origin.via}</dd>
                </div>
                {scrapedBoard ? (
                  <div className="flex justify-between gap-3">
                    <dt className="text-on-surface-variant">Scraped site</dt>
                    <dd className="font-medium capitalize">{scrapedBoard}</dd>
                  </div>
                ) : null}
                <div className="flex justify-between gap-3">
                  <dt className="text-on-surface-variant">Listing ID</dt>
                  <dd className="truncate font-mono text-[11px]">{job.external_id || "n/a"}</dd>
                </div>
                <div className="flex justify-between gap-3">
                  <dt className="text-on-surface-variant">Saved</dt>
                  <dd>{formatSavedAt(job.created_at)}</dd>
                </div>
                {job.url && !job.url.toLowerCase().includes("glassdoor.") ? (
                  <div className="flex justify-between gap-3">
                    <dt className="text-on-surface-variant">Original URL</dt>
                    <dd className="max-w-[60%] truncate">
                      <a className="text-primary underline" href={job.url} target="_blank" rel="noreferrer">
                        Open source
                      </a>
                    </dd>
                  </div>
                ) : null}
              </dl>
            </details>
          </div>
        </div>
        <div className="flex min-w-0 flex-col justify-center gap-2 lg:col-span-4">
          {job.url && !job.url.toLowerCase().includes("glassdoor.") ? (
            <a className="btn-primary w-full" href={job.url} target="_blank" rel="noreferrer">
              Open posting
            </a>
          ) : null}
        </div>
      </div>
    </article>
  );
}
