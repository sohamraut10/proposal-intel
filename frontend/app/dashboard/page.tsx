"use client";
import { useState, useMemo } from "react";
import AppLayout from "@/components/layout";
import FilterPanel, { type Filters } from "@/components/filter-panel";
import JobCard, { type Job } from "@/components/job-card";
import { useAuth, useJobs } from "@/lib/hooks";
import { api } from "@/lib/api";
import { formatBudget, formatRelativeTime, scoreColor, cn } from "@/lib/utils";

const DEFAULT_FILTERS: Filters = {
  min_score: 0,
  platform: "",
  category: "",
  budget_min: "",
  budget_max: "",
  qualified_only: false,
};

export default function DashboardPage() {
  useAuth();
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [selected, setSelected] = useState<Job | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<{
    win_probability?: number;
    quality_score?: number;
    bid_amount?: number;
    cover_letter?: string;
    proposal_text?: string;
  } | null>(null);
  const [strategy, setStrategy] = useState("standard");
  const [refreshing, setRefreshing] = useState(false);

  const queryParams = useMemo(() => {
    const p: Record<string, string | number | boolean> = {};
    if (filters.min_score > 0) p.min_score = filters.min_score;
    if (filters.platform) p.platform = filters.platform;
    if (filters.qualified_only) p.qualified_only = true;
    if (filters.budget_min) p.budget_min = filters.budget_min;
    return p;
  }, [filters]);

  const { jobs, loading, reload } = useJobs(queryParams);

  const filteredJobs = useMemo(() => {
    let list = jobs as Job[];
    if (filters.category) list = list.filter(j => j.category?.toLowerCase().includes(filters.category));
    if (filters.budget_max) list = list.filter(j => (j.budget_min ?? 0) <= Number(filters.budget_max));
    return list;
  }, [jobs, filters.category, filters.budget_max]);

  async function handleRefresh() {
    setRefreshing(true);
    try { await api.refreshJobs(); await reload(); } finally { setRefreshing(false); }
  }

  async function handleGenerate() {
    if (!selected) return;
    setGenerating(true);
    setGenerated(null);
    try {
      const result = await api.generateProposal(selected.id, strategy);
      setGenerated(result);
    } catch (e: unknown) {
      alert((e as Error).message);
    } finally {
      setGenerating(false);
    }
  }

  return (
    <AppLayout>
      <div className="flex h-screen overflow-hidden">
        {/* Filter panel */}
        <FilterPanel filters={filters} onChange={setFilters} />

        {/* Jobs list */}
        <div
          className="w-80 shrink-0 flex flex-col border-r overflow-hidden"
          style={{ borderColor: "var(--color-slate-800)" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b shrink-0"
            style={{ borderColor: "var(--color-slate-800)" }}>
            <h1 className="text-sm font-semibold text-white">
              Jobs <span className="text-slate-500 font-mono">({filteredJobs.length})</span>
            </h1>
            <button
              onClick={handleRefresh}
              disabled={refreshing}
              className="text-xs px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50"
              style={{ background: "var(--color-indigo)", color: "white" }}
            >
              {refreshing ? "…" : "Refresh"}
            </button>
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto p-3 flex flex-col gap-2">
            {loading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="h-24 rounded-xl animate-pulse-slow"
                  style={{ background: "var(--color-slate-800)" }} />
              ))
            ) : filteredJobs.length === 0 ? (
              <div className="text-center py-16 text-sm" style={{ color: "var(--color-slate-400)" }}>
                No jobs found.<br />
                <button onClick={handleRefresh} className="underline mt-1" style={{ color: "var(--color-indigo)" }}>
                  Fetch from platforms
                </button>
              </div>
            ) : (
              filteredJobs.map((job, i) => (
                <JobCard
                  key={job.id}
                  job={job}
                  index={i}
                  selected={selected?.id === job.id}
                  onClick={() => { setSelected(job); setGenerated(null); }}
                />
              ))
            )}
          </div>
        </div>

        {/* Detail panel */}
        <div className="flex-1 overflow-y-auto">
          {!selected ? (
            <div className="flex items-center justify-center h-full"
              style={{ color: "var(--color-slate-400)" }}>
              <div className="text-center">
                <div className="text-4xl mb-3">👈</div>
                <p className="text-sm">Select a job to view details</p>
              </div>
            </div>
          ) : (
            <div className="p-6 max-w-2xl mx-auto">
              {/* Job header */}
              <div className="mb-6">
                <div className="flex items-start justify-between gap-4 mb-2">
                  <h2 className="text-xl font-bold text-white">{selected.title}</h2>
                  <span className={cn("text-lg font-bold tabular-nums px-3 py-1 rounded-lg border shrink-0", scoreColor(selected.score_total))}>
                    {Math.round(selected.score_total)}
                  </span>
                </div>
                <div className="flex flex-wrap gap-3 text-sm mb-4" style={{ color: "var(--color-slate-400)", fontFamily: "Fira Code" }}>
                  <span>{formatBudget(selected.budget_min, selected.budget_max)} {selected.budget_type}</span>
                  {selected.client_rating && <span>⭐ {selected.client_rating.toFixed(1)}</span>}
                  {selected.client_jobs_posted && <span>{selected.client_jobs_posted} jobs posted</span>}
                  {selected.client_name && <span>{selected.client_name}</span>}
                  {selected.posted_at && <span>{formatRelativeTime(selected.posted_at)}</span>}
                </div>
                {selected.url && (
                  <a href={selected.url} target="_blank" rel="noreferrer"
                    className="text-xs underline" style={{ color: "var(--color-indigo)" }}>
                    View on {selected.platform} →
                  </a>
                )}
              </div>

              {/* Description */}
              <div className="rounded-xl p-4 mb-6 border"
                style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}>
                <p className="text-xs font-semibold uppercase tracking-widest mb-3"
                  style={{ color: "var(--color-slate-400)" }}>Description</p>
                <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
                  {selected.description || "No description provided."}
                </p>
              </div>

              {/* Generate proposal */}
              <div className="rounded-xl border p-4"
                style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}>
                <p className="text-xs font-semibold uppercase tracking-widest mb-3"
                  style={{ color: "var(--color-slate-400)" }}>Generate Proposal</p>

                <div className="flex gap-2 mb-3">
                  {(["standard", "aggressive", "cautious"] as const).map(s => (
                    <button
                      key={s}
                      onClick={() => setStrategy(s)}
                      className="px-3 py-1 rounded-lg text-xs capitalize transition-all border"
                      style={{
                        background: strategy === s ? "var(--color-indigo)" : "transparent",
                        borderColor: strategy === s ? "var(--color-indigo)" : "var(--color-slate-700)",
                        color: strategy === s ? "white" : "var(--color-slate-400)",
                      }}
                    >
                      {s}
                    </button>
                  ))}
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={generating}
                  className="w-full py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
                  style={{ background: "var(--color-indigo)", color: "white" }}
                >
                  {generating ? "Generating…" : "Generate with GPT-4o"}
                </button>

                {generated && (
                  <div className="mt-4 animate-fade-in">
                    {/* Metrics */}
                    <div className="grid grid-cols-3 gap-2 mb-3">
                      {[
                        { label: "Win %", value: `${Math.round((generated.win_probability ?? 0) * 100)}%` },
                        { label: "Quality", value: generated.quality_score ? `${generated.quality_score}/100` : "—" },
                        { label: "Bid", value: generated.bid_amount ? `$${generated.bid_amount}` : "—" },
                      ].map(({ label, value }) => (
                        <div key={label} className="rounded-lg p-2 text-center border"
                          style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)" }}>
                          <p className="text-xs text-slate-400">{label}</p>
                          <p className="text-sm font-bold text-white tabular-nums">{value}</p>
                        </div>
                      ))}
                    </div>

                    {/* Cover letter */}
                    {generated.cover_letter && (
                      <div className="rounded-lg p-3 mb-3 border text-xs"
                        style={{ background: "var(--color-indigo)" + "20", borderColor: "var(--color-indigo)" + "40", color: "#c7d2fe" }}>
                        <p className="font-semibold mb-1 text-indigo-300">Cover letter</p>
                        {generated.cover_letter as string}
                      </div>
                    )}

                    {/* Proposal */}
                    <div className="relative">
                      <pre className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed p-3 rounded-lg border overflow-auto max-h-72"
                        style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", fontFamily: "Inter" }}>
                        {generated.proposal_text as string}
                      </pre>
                      <button
                        onClick={() => navigator.clipboard.writeText(generated.proposal_text as string)}
                        className="absolute top-2 right-2 text-xs px-2 py-1 rounded border transition-colors"
                        style={{ background: "var(--color-slate-700)", borderColor: "var(--color-slate-600)", color: "var(--color-slate-300)" }}
                      >
                        Copy
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
