export type AspectRatio = "9:16" | "16:9" | "4:5" | "1:1";
export type RenderStatus = "queued" | "rendering" | "completed" | "failed";

export interface Clip {
  id: number;
  project_id: number;
  highlight_moment_id: number;
  aspect_ratio: AspectRatio;
  crop_mode: string;
  output_path: string | null;
  resolution: string | null;
  duration_seconds: number | null;
  render_status: RenderStatus;
  render_error_message: string | null;
  created_at: string;
  updated_at: string;
}
