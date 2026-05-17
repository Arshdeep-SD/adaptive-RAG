import type { IngestResponse, JobResponse, QueryResponse, TokenResponse, UISchema, UserResponse, UserRole } from "../types/ui";

export const BASE = import.meta.env.VITE_API_URL ?? "";

/** Prepend the API base to a path — use for img/audio src attributes. */
export function apiUrl(path: string): string {
  return `${BASE}${path}`;
}

// ---------------------------------------------------------------------------
// Token management
// ---------------------------------------------------------------------------

const TOKEN_KEY = "auth_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// Core request helper — injects Bearer token, handles 401
// ---------------------------------------------------------------------------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const existingHeaders = (init?.headers ?? {}) as Record<string, string>;
  const headers: Record<string, string> = { ...existingHeaders };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers });

  if (res.status === 401) {
    clearToken();
    throw new Error("UNAUTHORIZED");
  }

  // 204 No Content — no body to parse
  if (res.status === 204) {
    return undefined as unknown as T;
  }

  const body = await res.json();
  if (!res.ok) {
    const msg = body?.detail ?? body?.error?.message ?? `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return body as T;
}

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------

export const api = {
  // Auth
  login: (username: string, password: string): Promise<TokenResponse> => {
    const form = new URLSearchParams({ username, password });
    return request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
  },

  listUsers: (): Promise<UserResponse[]> => request("/auth/users"),

  createUser: (username: string, password: string, role: UserRole): Promise<UserResponse> =>
    request("/auth/users", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, role }),
    }),

  deleteUser: (userId: string): Promise<void> =>
    request(`/auth/users/${userId}`, { method: "DELETE" }),

  // Ingest
  ingestFile: (file: File): Promise<IngestResponse> => {
    const form = new FormData();
    form.append("file", file);
    return request("/ingest", { method: "POST", body: form });
  },

  ingestJson: (data: object, sourceLabel: string): Promise<IngestResponse> =>
    request("/ingest/json", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data, source_label: sourceLabel }),
    }),

  ingestUrl: (url: string, sourceLabel?: string): Promise<IngestResponse> =>
    request("/ingest/url", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, source_label: sourceLabel }),
    }),

  // Jobs
  listJobs: (): Promise<JobResponse[]> => request("/jobs"),

  getJob: (jobId: string): Promise<JobResponse> => request(`/jobs/${jobId}`),

  deleteJob: (jobId: string): Promise<void> =>
    request(`/jobs/${jobId}`, { method: "DELETE" }),

  setJobVisibility: (jobId: string, visibility: "private" | "public"): Promise<JobResponse> =>
    request(`/jobs/${jobId}/visibility`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ visibility }),
    }),

  // Query
  query: (query: string, topK = 5): Promise<QueryResponse> =>
    request("/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, top_k: topK }),
    }),

  generateUISchema: (
    data: object,
    intent?: string
  ): Promise<{ ui_schema: UISchema }> =>
    request("/ui-schema", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ data, intent }),
    }),

  getRecord: (recordId: string): Promise<{ record_id: string; text: string }> =>
    request(`/records/${recordId}`),
};
