import { useMemo } from "react";

import type { Job, JobFilter } from "../types";

export const JOB_FILTERS: JobFilter[] = ["ALL", "APPLY", "MAYBE", "SKIP"];

export function useJobs(jobs: Job[], filter: JobFilter) {
  const visibleJobs = useMemo(() => {
    if (filter === "ALL") return jobs;
    return jobs.filter((job) => job.fit?.recommendation === filter);
  }, [jobs, filter]);

  return { jobs, visibleJobs, filter, filters: JOB_FILTERS };
}
