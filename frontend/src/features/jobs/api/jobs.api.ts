import { api } from "../../../api.js";
import type { Job, JobFilter, SearchStart } from "../types";

export type ListJobsParams = {
  recommendation?: Exclude<JobFilter, "ALL">;
  min_score?: number | string;
};

export const jobsApi = {
  list: (params: ListJobsParams = {}) => api.listJobs(params) as Promise<Job[]>,
  startSearch: () => api.startSearch() as Promise<SearchStart>,
  getSearch: (id: string) => api.getSearch(id),
  prepare: (id: string) => api.prepareJob(id) as Promise<SearchStart>,
};
