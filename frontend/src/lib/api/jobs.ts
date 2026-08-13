import { get, post, put, del } from "../api/client";

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

export interface JobAcceptedResponse {
  job_id: number;
  message: string;
}

export function fetchJobs(projectId?: number): Promise<Job[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return get<Job[]>(`/jobs${query}`);
}

export function fetchJob(id: number): Promise<Job> {
  return get<Job>(`/jobs/${id}`);
}

export function listApiKeys() {
  return get<any[]>("/api-keys");
}

export function createApiKey(payload: {
  service_name: string;
  api_key_value: string;
}) {
  return post<any>("/api-keys", payload);
}

export function updateApiKey(
  id: number,
  payload: { service_name: string; api_key_value: string },
) {
  return put<any>(`/api-keys/${id}`, payload);
}

export function deleteApiKey(id: number) {
  return del<void>(`/api-keys/${id}`);
}

export function toggleApiKey(id: number) {
  return post<any>(`/api-keys/${id}/toggle`);
}
