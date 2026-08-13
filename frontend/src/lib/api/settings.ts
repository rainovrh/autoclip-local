import { get } from "../api/client";

export interface HealthResponse {
  status: string;
  message: string;
}

export function fetchHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/settings/health");
}
