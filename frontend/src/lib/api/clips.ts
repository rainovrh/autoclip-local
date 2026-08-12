import { request } from "./client";
import type { Clip } from "@/types/clip.types";

export function fetchClips(projectId?: number): Promise<Clip[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return request<Clip[]>(`/clips${query}`);
}

export function fetchClip(id: number): Promise<Clip> {
  return request<Clip>(`/clips/${id}`);
}
