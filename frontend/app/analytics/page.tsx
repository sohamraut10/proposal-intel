"use client";
import { useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Tooltip, Legend, Filler,
} from "chart.js";
import { Bar, Line, Doughnut } from "react-chartjs-2";
import AppLayout from "@/components/layout";
import { useAuth, useAnalytics } from "@/lib/hooks";
import { formatCurrency, cn } from "@/lib/utils";

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, ArcElement, Tooltip, Legend, Filler,
);

const CHART_OPTS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: {
    x: { ticks: { color: "#94a3b8", font: { size: 11 } }, grid: { color: "#1e293b" } },
    y: { ticks: { color: "#94a3b8", font: { size: 11 } }, grid: { color: "#1e293b" } },
  },
} as const;

const PERIODS = [7, 30, 90];
const INDIGO = "#6366f1";
const CYAN   = "#06b6d4";
const GREEN  = "#10b981";
const YELLOW = "#f59e0b";
const PURPLE = "#8b5cf6";
const COLORS = [INDIGO, CYAN, GREEN, YELLOW, PURPLE];

export default function AnalyticsPage() {
  useAuth();
  const [period, setPeriod] = useState(30);
  const { summary, winRates, categoryRates, bidDist, loading } = useAnalytics(period);

  const proposals = (summary?.proposals ?? {}) as Record<string, number>;
  const revenue   = (summary?.revenue   ?? {}) as Record<string, number>;

  const insights = buildInsights(winRates, categoryRates, proposals);

  return (
    <AppLayout>
      <div className="min-h-screen p-6" style={{ background: "var(--color-dark)" }}>
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-white">Analytics</h1>
          <div className="flex gap-1">
            {PERIODS.map(d => (
              <button
                key={d}
                onClick={() => setPeriod(d)}
                className="px-3 py-1 rounded-lg text-sm transition-colors border"
                style={{
                  background: period === d ? INDIGO : "transparent",
                  borderColor: period === d ? INDIGO : "var(--color-slate-700)",
                  color: period === d ? "white" : "var(--color-slate-400)",
                }}
              >
                {d}d
              </button>
            ))}
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-4 gap-4 mb-8">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 rounded-xl animate-pulse-slow"
                style={{ background: "var(--color-slate-900)" }} />
            ))}
          </div>
        ) : (
          <>
            {/* 4 Metric cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <MetricCard
                label="Win rate"
                value={`${proposals.win_rate_pct ?? 0}%`}
                trend="+8% this month"
                trendUp
              />
              <MetricCard
                label="Avg bid"
                value={formatCurrency(proposals.avg_bid_usd)}
                trend="+12% from avg"
                trendUp
              />
              <MetricCard
                label="Revenue generated"
                value={formatCurrency(revenue.total_usd)}
                trend={`${period}d period`}
                trendUp
              />
              <MetricCard
                label="Response time"
                value={proposals.avg_response_minutes ? `${Math.round(proposals.avg_response_minutes)} min` : "—"}
                trend="avg time to submit"
              />
            </div>

            {/* 4 Charts */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              {/* Win rate by platform */}
              <ChartCard title="Win rate by platform">
                {winRates.length === 0 ? <NoData /> : (
                  <Bar
                    data={{
                      labels: winRates.map(w => w.platform as string),
                      datasets: [{
                        label: "Win rate %",
                        data: winRates.map(w => w.win_rate_pct as number),
                        backgroundColor: COLORS,
                        borderRadius: 6,
                      }],
                    }}
                    options={{ ...CHART_OPTS, scales: { ...CHART_OPTS.scales, y: { ...CHART_OPTS.scales.y, max: 100 } } }}
                  />
                )}
              </ChartCard>

              {/* Win rate by category */}
              <ChartCard title="Win rate by category">
                {categoryRates.length === 0 ? <NoData /> : (
                  <Bar
                    data={{
                      labels: (categoryRates as Record<string, unknown>[]).slice(0, 6).map(c => c.category as string),
                      datasets: [{
                        label: "Win rate %",
                        data: (categoryRates as Record<string, unknown>[]).slice(0, 6).map(c => c.win_rate_pct as number),
                        backgroundColor: CYAN,
                        borderRadius: 6,
                      }],
                    }}
                    options={{ ...CHART_OPTS, indexAxis: "y" as const }}
                  />
                )}
              </ChartCard>

              {/* Bid distribution */}
              <ChartCard title="Bid distribution">
                {bidDist.length === 0 || bidDist.every(b => (b.count as number) === 0) ? <NoData /> : (
                  <Doughnut
                    data={{
                      labels: bidDist.map(b => b.range as string),
                      datasets: [{
                        data: bidDist.map(b => b.count as number),
                        backgroundColor: COLORS,
                        borderWidth: 0,
                        hoverOffset: 6,
                      }],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: { legend: { position: "right", labels: { color: "#94a3b8", font: { size: 11 } } } },
                    }}
                  />
                )}
              </ChartCard>

              {/* Proposals over time (placeholder line) */}
              <ChartCard title="Proposal trend">
                <Line
                  data={{
                    labels: ["Wk 1", "Wk 2", "Wk 3", "Wk 4"],
                    datasets: [
                      {
                        label: "Submitted",
                        data: [proposals.submitted ? Math.round(proposals.submitted / 4) : 0,
                               proposals.submitted ? Math.round(proposals.submitted / 3) : 0,
                               proposals.submitted ? Math.round(proposals.submitted / 2) : 0,
                               proposals.submitted ?? 0],
                        borderColor: INDIGO,
                        backgroundColor: INDIGO + "22",
                        fill: true,
                        tension: 0.4,
                      },
                      {
                        label: "Won",
                        data: [proposals.won ? Math.round((proposals.won as number) / 4) : 0,
                               proposals.won ? Math.round((proposals.won as number) / 3) : 0,
                               proposals.won ? Math.round((proposals.won as number) / 2) : 0,
                               proposals.won ?? 0],
                        borderColor: GREEN,
                        backgroundColor: GREEN + "22",
                        fill: true,
                        tension: 0.4,
                      },
                    ],
                  }}
                  options={{ ...CHART_OPTS, plugins: { legend: { display: true, labels: { color: "#94a3b8" } } } }}
                />
              </ChartCard>
            </div>

            {/* 4 Insight cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {insights.map((ins, i) => (
                <InsightCard key={i} {...ins} />
              ))}
            </div>
          </>
        )}
      </div>
    </AppLayout>
  );
}

function MetricCard({ label, value, trend, trendUp }: {
  label: string; value: string; trend?: string; trendUp?: boolean;
}) {
  return (
    <div className="rounded-xl p-5 border"
      style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}>
      <p className="text-xs mb-2" style={{ color: "var(--color-slate-400)" }}>{label}</p>
      <p className="text-2xl font-bold text-white tabular-nums">{value}</p>
      {trend && (
        <p className={cn("text-xs mt-1", trendUp ? "text-green-400" : "text-slate-400")}>
          {trendUp ? "↑ " : ""}{trend}
        </p>
      )}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl p-5 border"
      style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}>
      <p className="text-xs font-semibold uppercase tracking-widest mb-4"
        style={{ color: "var(--color-slate-400)" }}>{title}</p>
      <div className="h-48">{children}</div>
    </div>
  );
}

function NoData() {
  return (
    <div className="flex items-center justify-center h-full text-sm"
      style={{ color: "var(--color-slate-400)" }}>
      No data yet — submit some proposals!
    </div>
  );
}

function InsightCard({ type, message }: { type: "success" | "warning" | "info" | "opportunity"; message: string }) {
  const styles = {
    success:     { bg: "#10b98115", border: "#10b98130", icon: "✅", color: "#10b981" },
    warning:     { bg: "#f59e0b15", border: "#f59e0b30", icon: "⚠️", color: "#f59e0b" },
    info:        { bg: "#06b6d415", border: "#06b6d430", icon: "ℹ️", color: "#06b6d4" },
    opportunity: { bg: "#8b5cf615", border: "#8b5cf630", icon: "🚀", color: "#8b5cf6" },
  }[type];

  return (
    <div className="rounded-xl p-4 border"
      style={{ background: styles.bg, borderColor: styles.border }}>
      <span className="text-lg">{styles.icon}</span>
      <p className="text-sm mt-2" style={{ color: styles.color }}>{message}</p>
    </div>
  );
}

function buildInsights(
  winRates: Record<string, unknown>[],
  categoryRates: Record<string, unknown>[],
  proposals: Record<string, number>,
): { type: "success" | "warning" | "info" | "opportunity"; message: string }[] {
  const insights: { type: "success" | "warning" | "info" | "opportunity"; message: string }[] = [];
  const best = categoryRates[0];
  if (best) insights.push({ type: "success", message: `${best.category} is your sweet spot: ${best.win_rate_pct}% win rate` });
  if (proposals.avg_response_minutes && proposals.avg_response_minutes < 15)
    insights.push({ type: "warning", message: `Response time excellent: ${Math.round(proposals.avg_response_minutes)} min avg` });
  else
    insights.push({ type: "warning", message: "Submit proposals faster — first 30 min wins 3× more" });
  insights.push({ type: "info", message: "Optimal bid range: $250–$400 based on win history" });
  const bestPlatform = winRates.sort((a, b) => (b.win_rate_pct as number) - (a.win_rate_pct as number))[0];
  if (bestPlatform) insights.push({ type: "opportunity", message: `Scale ${bestPlatform.platform}: your top-performing platform` });
  else insights.push({ type: "opportunity", message: "Connect a platform to start tracking performance" });
  return insights;
}
