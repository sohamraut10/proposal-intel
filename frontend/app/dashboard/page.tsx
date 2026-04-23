"use client";
import { useEffect, useState } from "react";
import AppLayout from "@/components/layout";
import { api } from "@/lib/api";

type Job = {
  id: string;
  platform: string;
  title: string;
  description: string | null;
  category: string | null;
  budget_min: number | null;
  budget_max: number | null;
  budget_type: string | null;
  client_country: string | null;
  client_rating: number | null;
  proposals_count: number;
  score_total: number;
  is_qualified: boolean;
  url: string | null;
};

const PLATFORM_COLORS: Record<string, string> = {
  upwork: "bg-green-700",
  freelancer: "bg-blue-700",
  pph: "bg-orange-700",
};

export default function DashboardPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [qualifiedOnly, setQualifiedOnly] = useState(false);
  const [platform, setPlatform] = useState("");
  const [generating, setGenerating] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    try {
      const params: Record<string, string | boolean> = {};
      if (qualifiedOnly) params.qualified_only = true;
      if (platform) params.platform = platform;
      const data = await api.listJobs(params);
      setJobs(data as Job[]);
    } catch {
      // ignore auth errors — redirect handled globally
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [qualifiedOnly, platform]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleGenerate(jobId: string) {
    setGenerating(jobId);
    try {
      await api.generateProposal(jobId);
      alert("Proposal generated — check the Proposals page!");
    } catch (e: unknown) {
      alert((e as Error).message);
    } finally {
      setGenerating(null);
    }
  }

  async function handleRefresh() {
    setLoading(true);
    try {
      await api.refreshJobs();
      await load();
    } catch (e: unknown) {
      alert((e as Error).message);
      setLoading(false);
    }
  }

  return (
    <AppLayout>
      <div className="p-6 bg-gray-950 min-h-screen">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-white">Job Discovery</h1>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-sm font-medium"
          >
            Refresh Jobs
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-3 mb-6">
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input
              type="checkbox"
              checked={qualifiedOnly}
              onChange={(e) => setQualifiedOnly(e.target.checked)}
              className="rounded"
            />
            Qualified only
          </label>
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="bg-gray-800 text-gray-200 rounded-lg px-3 py-1 text-sm border border-gray-700"
          >
            <option value="">All platforms</option>
            <option value="upwork">Upwork</option>
            <option value="freelancer">Freelancer</option>
            <option value="pph">PeoplePerHour</option>
          </select>
        </div>

        {loading ? (
          <div className="text-gray-400 text-center py-20">Loading jobs…</div>
        ) : jobs.length === 0 ? (
          <div className="text-gray-500 text-center py-20">
            No jobs found. Hit Refresh to fetch from platforms.
          </div>
        ) : (
          <div className="grid gap-4">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="bg-gray-900 border border-gray-800 rounded-xl p-5 hover:border-gray-700 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`text-xs font-medium px-2 py-0.5 rounded ${
                          PLATFORM_COLORS[job.platform] ?? "bg-gray-700"
                        }`}
                      >
                        {job.platform}
                      </span>
                      {job.is_qualified && (
                        <span className="text-xs font-medium px-2 py-0.5 rounded bg-emerald-700">
                          Qualified
                        </span>
                      )}
                      <span className="text-xs text-gray-500">{job.category}</span>
                    </div>
                    <h2 className="text-base font-semibold text-white truncate">{job.title}</h2>
                    <p className="text-sm text-gray-400 mt-1 line-clamp-2">{job.description}</p>
                    <div className="flex gap-4 mt-2 text-xs text-gray-500">
                      {job.budget_min != null && (
                        <span>
                          ${job.budget_min}–${job.budget_max} {job.budget_type}
                        </span>
                      )}
                      {job.client_country && <span>{job.client_country}</span>}
                      <span>{job.proposals_count} proposals</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    <div className="text-2xl font-bold text-indigo-400">{job.score_total.toFixed(0)}</div>
                    <div className="text-xs text-gray-500">score</div>
                    <button
                      onClick={() => handleGenerate(job.id)}
                      disabled={generating === job.id}
                      className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 rounded-lg text-xs font-medium"
                    >
                      {generating === job.id ? "Generating…" : "Generate"}
                    </button>
                    {job.url && (
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs text-indigo-400 hover:underline"
                      >
                        View →
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
