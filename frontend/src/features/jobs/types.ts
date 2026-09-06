export type FitRecommendation = "APPLY" | "MAYBE" | "SKIP";

export type JobFilter = "ALL" | FitRecommendation;

export type JobFit = {
  overall_score?: number | null;
  recommendation?: FitRecommendation | string;
  skill_match_score?: number;
  experience_match_score?: number;
  role_match_score?: number;
  education_match_score?: number;
  location_match_score?: number;
  matched_skills?: string[];
  missing_required_skills?: string[];
  strengths?: string[];
  gaps?: string[];
  reasoning?: string;
  experience_assessment?: string;
  critical_gaps?: string[];
};

export type Job = {
  id: string;
  source?: string;
  external_id?: string;
  title?: string;
  company?: string;
  location?: string;
  description?: string;
  url?: string;
  created_at?: string | null;
  application_id?: string | null;
  application_status?: string | null;
  fit?: JobFit | null;
};

export type SearchStart = {
  id: string;
  status: string;
};
