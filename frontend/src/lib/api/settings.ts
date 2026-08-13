import { get, post, put, del, patch } from "../api/client";

export interface HealthResponse {
  status: string;
  message: string;
}

export function fetchHealth(): Promise<HealthResponse> {
  return get<HealthResponse>("/settings/health");
}

export function listApiKeys() {
  return get<any[]>("/api-keys");
}

export function createApiKey(payload: {
  service_name: string;
  api_key_value: string;
}) {
  return post<any>("/api-keys", payload);
}

export function updateApiKey(
  id: number,
  payload: { service_name: string; api_key_value: string },
) {
  return put<any>(`/api-keys/${id}`, payload);
}

export function deleteApiKey(id: number) {
  return del<void>(`/api-keys/${id}`);
}

export function toggleApiKey(id: number) {
  return patch<any>(`/api-keys/${id}/toggle`);
}
