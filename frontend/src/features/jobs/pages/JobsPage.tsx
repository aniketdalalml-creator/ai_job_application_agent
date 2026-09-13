import JobFilters from "../components/JobFilters";
import JobList from "../components/JobList";
import { useJobs } from "../hooks/useJobs";
import type { Job, JobFilter } from "../types";

export type JobsPageProps = {
  jobs: Job[];
  filter: JobFilter;
  setFilter: (filter: JobFilter) => void;
  searching: boolean;
  error: string;
  onSearch: () => void;
};

export default function JobsPage({
  jobs,
  filter,
  setFilter,
  searching,
  error,
  onSearch,
}: JobsPageProps) {
  const { visibleJobs } = useJobs(jobs, filter);

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
            Search uses your saved profile. Each posting is scored APPLY / MAYBE / SKIP.
          </p>
        </div>
        <button type="button" className="btn-primary" onClick={onSearch} disabled={searching}>
          <span className="material-symbols-outlined text-[18px]">travel_explore</span>
          {searching ? "Searching..." : "Find jobs"}
        </button>
      </div>

      <JobFilters filter={filter} onChange={setFilter} />

      {error ? <p className="text-[13px] font-medium text-error">{error}</p> : null}

      <JobList jobs={visibleJobs} />
    </div>
  );
}
