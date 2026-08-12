export type ProjectStatus =
  | "UPLOADED"
  | "AUDIO_EXTRACTED"
  | "TRANSCRIBED"
  | "ANALYZED"
  | "RENDERED"
  | "FAILED";

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
