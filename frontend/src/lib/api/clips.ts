import { get, put } from "../api/client";
import type { Clip, SubtitleStyleResponse } from "@/types/clip.types";

export function fetchClips(projectId?: number): Promise<Clip[]> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return get<Clip[]>(`/clips${query}`);
}

export function fetchClip(id: number): Promise<Clip> {
  return get<Clip>(`/clips/${id}`);
}

export function updateSubtitleStyle(
  clipId: number,
  style: Record<string, unknown>,
): Promise<SubtitleStyleResponse> {
  return put<SubtitleStyleResponse>(`/clips/${clipId}/subtitle-style`, style);
}

export function downloadClip(clipId: number): Promise<void> {
  return get<void>(`/clips/${clipId}/download`);
}
