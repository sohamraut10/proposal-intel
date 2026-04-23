const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

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
  login: (email: string, password: string) => {
    const body = new URLSearchParams({ username: email, password });
    return request<{ access_token: string }>("/auth/token", {
      method: "POST",
      body,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
  register: (email: string, password: string, full_name?: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  // Users
  getMe: () => request<Record<string, unknown>>("/users/me"),
  updateMe: (data: Record<string, unknown>) =>
    request("/users/me", { method: "PATCH", body: JSON.stringify(data) }),

  // Jobs
  listJobs: (params?: Record<string, string | number | boolean>) => {
    const qs = params ? "?" + new URLSearchParams(params as Record<string, string>).toString() : "";
    return request<Record<string, unknown>[]>(`/jobs/${qs}`);
  },
  getJob: (id: string) => request<Record<string, unknown>>(`/jobs/${id}`),
  refreshJobs: (query = "") => request(`/jobs/refresh?query=${encodeURIComponent(query)}`, { method: "POST" }),

  // Proposals
  generateProposal: (job_id: string, bid_amount?: number, bid_type?: string) =>
    request<Record<string, unknown>>("/proposals/generate", {
      method: "POST",
      body: JSON.stringify({ job_id, bid_amount, bid_type }),
    }),
  listProposals: (status?: string) =>
    request<Record<string, unknown>[]>(`/proposals/${status ? `?status=${status}` : ""}`),
  updateProposal: (id: string, data: Record<string, unknown>) =>
    request(`/proposals/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Analytics
  getSummary: () => request<Record<string, unknown>>("/analytics/summary"),
  getWinRates: () => request<Record<string, unknown>[]>("/analytics/win-rates-by-platform"),
  getScoreDistribution: () => request<Record<string, unknown>[]>("/analytics/score-distribution"),
};
