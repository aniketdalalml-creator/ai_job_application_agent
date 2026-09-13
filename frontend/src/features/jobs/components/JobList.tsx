import type { Job } from "../types";
import JobCard from "./JobCard";

type JobListProps = {
  jobs: Job[];
};

export default function JobList({ jobs }: JobListProps) {
  if (jobs.length === 0) {
    return (
      <div className="institutional-panel p-10 text-center text-on-surface-variant">
        No jobs yet. Save a profile, then run Find jobs.
      </div>
    );
  }

  return (
    <div className="grid w-full grid-cols-1 gap-4">
      {jobs.map((job) => (
        <JobCard key={job.id} job={job} />
      ))}
    </div>
  );
}
