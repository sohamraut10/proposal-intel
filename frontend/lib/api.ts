import { getToken } from "./auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json() as Promise<T>;
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/token", {
      method: "POST",
      body: new URLSearchParams({ username: email, password }).toString(),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),
  register: (email: string, password: string, name?: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    }),

  // Users
  getMe: () => request<Record<string, unknown>>("/users/me"),
  updateMe: (data: Record<string, unknown>) =>
    request<Record<string, unknown>>("/users/me", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  // Freelancer profiles
  getProfile: () => request<Record<string, unknown>>("/profiles/me"),
  upsertProfile: (data: Record<string, unknown>) =>
    request<Record<string, unknown>>("/profiles/me", {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  // Jobs
  listJobs: (params?: Record<string, string | number | boolean>) => {
    const qs = params
      ? "?" + new URLSearchParams(params as Record<string, string>).toString()
      : "";
    return request<Record<string, unknown>[]>(`/jobs/${qs}`);
  },
  getJob: (id: string) => request<Record<string, unknown>>(`/jobs/${id}`),
  refreshJobs: (query = "") =>
    request(`/jobs/refresh?query=${encodeURIComponent(query)}`, { method: "POST" }),

  // Proposals
  generateProposal: (job_id: string, strategy = "standard") =>
    request<Record<string, unknown>>("/proposals/generate", {
      method: "POST",
      body: JSON.stringify({ job_id, strategy }),
    }),
  listProposals: (status?: string) =>
    request<Record<string, unknown>[]>(
      `/proposals/${status ? `?status=${status}` : ""}`
    ),
  getProposal: (id: string) => request<Record<string, unknown>>(`/proposals/${id}`),
  updateProposal: (id: string, data: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/proposals/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  recordOutcome: (id: string, status: string, actual_amount?: number, feedback?: string) =>
    request<Record<string, unknown>>(`/proposals/${id}/outcome`, {
      method: "POST",
      body: JSON.stringify({ status, actual_amount, feedback }),
    }),

  // Analytics
  getSummary: (period_days = 30) =>
    request<Record<string, unknown>>(`/analytics/summary?period_days=${period_days}`),
  getWinRates: () => request<Record<string, unknown>[]>("/analytics/win-rates-by-platform"),
  getCategoryRates: () =>
    request<Record<string, unknown>[]>("/analytics/win-rates-by-category"),
  getBidDistribution: () =>
    request<Record<string, unknown>[]>("/analytics/bid-distribution"),
  getScoreDistribution: () =>
    request<Record<string, unknown>[]>("/analytics/score-distribution"),
  getUsage: () => request<Record<string, unknown>[]>("/analytics/usage"),
};
