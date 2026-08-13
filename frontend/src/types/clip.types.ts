export interface Clip {
  id: number;
  project_id: number;
  highlight_moment_id: number;
  aspect_ratio: string;
  crop_mode: string;
  output_path: string | null;
  resolution: string | null;
  duration_seconds: number | null;
  render_status: string;
  render_error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface SubtitleStyleResponse {
  id: number;
  clip_id: number;
  display_mode: string;
  font_family: string;
  font_size: number;
  font_weight: string;
  is_uppercase: boolean;
  text_color: string;
  highlight_color: string;
  background_color: string | null;
  background_opacity: number | null;
}

export interface ClipResponse {
  id: number;
  project_id: number;
  highlight_moment_id: number;
  aspect_ratio: string;
  crop_mode: string;
  output_path: string | null;
  resolution: string | null;
  duration_seconds: number | null;
  render_status: string;
  render_error_message: string | null;
  created_at: string;
  updated_at: string;
}

export type AspectRatio = "9:16" | "16:9" | "4:5" | "1:1";
export type RenderStatus = "queued" | "rendering" | "completed" | "failed";
