import { get, post, del } from "../api/client";
import type {
  Project,
  ProjectCreatePayload,
  ProjectListResponse,
  VideoSourceResponse,
} from "@/types/project.types";

export function fetchProjects(): Promise<ProjectListResponse> {
  return get<ProjectListResponse>("/projects");
}

export function fetchProject(id: number): Promise<Project> {
  return get<Project>(`/projects/${id}`);
}

export function createProject(
  payload: ProjectCreatePayload,
): Promise<Project> {
  return post<Project>("/projects", payload);
}

export function deleteProject(id: number): Promise<void> {
  return del<void>(`/projects/${id}`);
}

export function uploadVideo(
  projectId: number,
  file: File,
): Promise<VideoSourceResponse> {
  const form = new FormData();
  form.append("file", file);
  return post<VideoSourceResponse>(`/projects/${projectId}/upload`, form);
}

export function downloadYoutube(projectId: number): Promise<VideoSourceResponse> {
  return post<VideoSourceResponse>(`/projects/${projectId}/download-youtube`);
}

export function extractAudio(projectId: number): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/extract-audio`);
}

export function transcribeProject(projectId: number): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/transcribe`);
}

export function analyzeProject(projectId: number): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/analyze`);
}

export function renderProject(projectId: number): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/render`);
}

export function searchBroll(projectId: number): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/broll`);
}

export function garbageCollect(projectId: number): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/gc`);
}

export function scheduleProjectJobs(
  projectId: number,
  payload: {
    job_types: string[];
    scheduled_at?: string;
    webhook_url?: string;
  },
): Promise<{ job_id: number }> {
  return post<{ job_id: number }>(`/projects/${projectId}/schedule`, payload);
}
