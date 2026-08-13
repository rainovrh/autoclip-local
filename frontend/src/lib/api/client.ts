const API_BASE = "/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);

  if (!response.ok) {
    let detail = `Request gagal: ${response.status}`;
    try {
      const json = await response.json();
      detail = typeof json.detail === "string" ? json.detail : detail;
    } catch {
      const text = await response.text();
      if (text) detail = text;
    }
    throw new Error(detail);
  }

  if (response.status === 204 || response.headers.get("content-length") === "0") {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export function get<T>(path: string, headers?: Record<string, string>): Promise<T> {
  return request<T>(path, { headers, method: "GET" });
}

export function post<T>(
  path: string,
  body?: unknown,
  headers?: Record<string, string>,
): Promise<T> {
  const isFormData = body instanceof FormData;
  return request<T>(path, {
    headers: isFormData
      ? headers
      : { "Content-Type": "application/json", ...headers },
    method: "POST",
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  });
}

export function put<T>(
  path: string,
  body?: unknown,
  headers?: Record<string, string>,
): Promise<T> {
  const isFormData = body instanceof FormData;
  return request<T>(path, {
    headers: isFormData
      ? headers
      : { "Content-Type": "application/json", ...headers },
    method: "PUT",
    body: isFormData ? body : body ? JSON.stringify(body) : undefined,
  });
}

export function del<T>(path: string, headers?: Record<string, string>): Promise<T> {
  return request<T>(path, { headers, method: "DELETE" });
}

export { API_BASE };
