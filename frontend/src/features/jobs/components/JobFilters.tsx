import type { JobFilter } from "../types";
import { JOB_FILTERS } from "../hooks/useJobs";

type JobFiltersProps = {
  filter: JobFilter;
  onChange: (filter: JobFilter) => void;
};

export default function JobFilters({ filter, onChange }: JobFiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {JOB_FILTERS.map((item) => (
        <button
          key={item}
          type="button"
          className={filter === item ? "btn-primary !py-1.5 !text-[12px]" : "btn-secondary !py-1.5 !text-[12px]"}
          onClick={() => onChange(item)}
        >
          {item}
        </button>
      ))}
    </div>
  );
}
