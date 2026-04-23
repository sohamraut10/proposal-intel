"use client";
import { useEffect, useState } from "react";
import AppLayout from "@/components/layout";
import { api } from "@/lib/api";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

type Summary = {
  proposals: { total: number; submitted: number; won: number; win_rate_pct: number };
  jobs: { total: number; qualified: number };
};

type WinRate = { platform: string; submitted: number; won: number; win_rate_pct: number };
type ScoreBucket = { range: string; count: number };

const COLORS = ["#6366f1", "#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"];

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [winRates, setWinRates] = useState<WinRate[]>([]);
  const [distribution, setDistribution] = useState<ScoreBucket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getSummary(), api.getWinRates(), api.getScoreDistribution()])
      .then(([s, w, d]) => {
        setSummary(s as Summary);
        setWinRates(w as WinRate[]);
        setDistribution(d as ScoreBucket[]);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <AppLayout>
        <div className="flex items-center justify-center h-screen bg-gray-950 text-gray-400">
          Loading analytics…
        </div>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="p-6 bg-gray-950 min-h-screen text-white">
        <h1 className="text-2xl font-bold mb-6">Analytics</h1>

        {/* Summary cards */}
        {summary && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total proposals" value={summary.proposals.total} />
            <StatCard label="Submitted" value={summary.proposals.submitted} />
            <StatCard label="Won" value={summary.proposals.won} />
            <StatCard label="Win rate" value={`${summary.proposals.win_rate_pct}%`} highlight />
          </div>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          {/* Win rates by platform */}
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Win rate by platform</h2>
            {winRates.length === 0 ? (
              <p className="text-gray-500 text-sm">No data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={winRates} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="platform" stroke="#6b7280" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} unit="%" />
                  <Tooltip
                    contentStyle={{ background: "#111827", border: "1px solid #374151" }}
                    labelStyle={{ color: "#e5e7eb" }}
                  />
                  <Bar dataKey="win_rate_pct" radius={[4, 4, 0, 0]}>
                    {winRates.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          {/* Score distribution */}
          <div className="bg-gray-900 rounded-xl p-5 border border-gray-800">
            <h2 className="text-sm font-semibold text-gray-300 mb-4">Job score distribution</h2>
            {distribution.every((d) => d.count === 0) ? (
              <p className="text-gray-500 text-sm">No jobs scored yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={distribution} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
                  <XAxis dataKey="range" stroke="#6b7280" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#6b7280" tick={{ fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{ background: "#111827", border: "1px solid #374151" }}
                    labelStyle={{ color: "#e5e7eb" }}
                  />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {distribution.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}

function StatCard({ label, value, highlight }: { label: string; value: number | string; highlight?: boolean }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-4">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${highlight ? "text-indigo-400" : "text-white"}`}>{value}</p>
    </div>
  );
}
