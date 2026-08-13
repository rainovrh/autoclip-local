export interface Project {
  id: number;
  title: string;
  folder_path: string;
  source_type: "youtube" | "local_upload";
  source_url: string | null;
  original_filename: string | null;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus =
  | "UPLOADED"
  | "AUDIO_EXTRACTED"
  | "TRANSCRIBED"
  | "ANALYZED"
  | "RENDERED"
  | "FAILED";

export interface ProjectCreatePayload {
  title: string;
  source_type: "youtube" | "local_upload";
  source_url?: string | null;
  original_filename?: string | null;
}

export interface ProjectListResponse {
  items: Project[];
  total: number;
}

export interface VideoSourceResponse {
  id: number;
  project_id: number;
  file_path: string;
  audio_path: string | null;
  resolution: string | null;
  duration_seconds: number | null;
  fps: number | null;
  quality_check_passed: boolean;
  created_at: string;
}
