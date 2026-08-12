import { request } from "./client";
import type { Project } from "@/types/project.types";

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export function fetchProjects(): Promise<ProjectListResponse> {
  return request<ProjectListResponse>("/projects");
}

export function fetchProject(id: number): Promise<Project> {
  return request<Project>(`/projects/${id}`);
}
