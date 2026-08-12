import { request } from "./client";

export interface HealthResponse {
  status: string;
  message: string;
}

export function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/settings/health");
}
