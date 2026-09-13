import { useMemo } from "react";

import type { Job, JobFilter } from "../types";

export const JOB_FILTERS: JobFilter[] = ["ALL", "APPLY", "MAYBE", "SKIP"];

export function isOpenablePosting(job: Job) {
  const board = (job.external_id || "").split(":")[0].toLowerCase();
  const url = (job.url || "").toLowerCase();
  return board !== "glassdoor" && !url.includes("glassdoor.");
}

export function useJobs(jobs: Job[], filter: JobFilter) {
  const visibleJobs = useMemo(() => {
    const openable = jobs.filter(isOpenablePosting);
    if (filter === "ALL") return openable;
    return openable.filter((job) => job.fit?.recommendation === filter);
  }, [jobs, filter]);

  return { jobs, visibleJobs, filter, filters: JOB_FILTERS };
}
