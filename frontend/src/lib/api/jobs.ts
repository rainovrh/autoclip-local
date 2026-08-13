import { get } from "../api/client";

export interface Job {
  id: number;
  project_id: number;
  job_type: string;
  status: string;
  priority: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
}

export function fetchJobs(projectId?: number): Promise<Job[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return get<Job[]>(`/jobs${query}`);
}

export function fetchJob(id: number): Promise<Job> {
  return get<Job>(`/jobs/${id}`);
}
