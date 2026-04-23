"use client";

export type Filters = {
  min_score: number;
  platform: string;
  category: string;
  budget_min: string;
  budget_max: string;
  qualified_only: boolean;
};

type Props = {
  filters: Filters;
  onChange: (f: Filters) => void;
};

const PLATFORMS = ["", "upwork", "freelancer", "pph"];
const CATEGORIES = [
  "", "writing", "copywriting", "translation", "data-entry",
  "web-development", "python", "javascript", "data science", "ai",
];

export default function FilterPanel({ filters, onChange }: Props) {
  const set = (key: keyof Filters, value: string | number | boolean) =>
    onChange({ ...filters, [key]: value });

  return (
    <aside
      className="w-56 shrink-0 flex flex-col gap-4 p-4 border-r overflow-y-auto"
      style={{ borderColor: "var(--color-slate-800)", background: "var(--color-slate-900)" }}
    >
      <h2 className="text-xs font-semibold uppercase tracking-widest" style={{ color: "var(--color-slate-400)" }}>
        Filters
      </h2>

      {/* Score slider */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">
          Min score — <span className="tabular-nums text-white">{filters.min_score}</span>
        </label>
        <input
          type="range" min={0} max={100} step={5}
          value={filters.min_score}
          onChange={e => set("min_score", Number(e.target.value))}
          className="w-full accent-indigo-500"
        />
        <div className="flex justify-between text-xs text-slate-600 mt-0.5">
          <span>0</span><span>100</span>
        </div>
      </div>

      {/* Platform */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">Platform</label>
        <select
          value={filters.platform}
          onChange={e => set("platform", e.target.value)}
          className="w-full text-sm rounded-lg px-2 py-1.5 border"
          style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "var(--color-white)" }}
        >
          {PLATFORMS.map(p => <option key={p} value={p}>{p || "All platforms"}</option>)}
        </select>
      </div>

      {/* Category */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">Category</label>
        <select
          value={filters.category}
          onChange={e => set("category", e.target.value)}
          className="w-full text-sm rounded-lg px-2 py-1.5 border"
          style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "var(--color-white)" }}
        >
          {CATEGORIES.map(c => <option key={c} value={c}>{c || "All categories"}</option>)}
        </select>
      </div>

      {/* Budget range */}
      <div>
        <label className="block text-xs text-slate-400 mb-1">Budget (USD)</label>
        <div className="flex gap-2">
          <input
            type="number" placeholder="Min"
            value={filters.budget_min}
            onChange={e => set("budget_min", e.target.value)}
            className="w-full text-sm rounded-lg px-2 py-1.5 border"
            style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "var(--color-white)" }}
          />
          <input
            type="number" placeholder="Max"
            value={filters.budget_max}
            onChange={e => set("budget_max", e.target.value)}
            className="w-full text-sm rounded-lg px-2 py-1.5 border"
            style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "var(--color-white)" }}
          />
        </div>
      </div>

      {/* Qualified only */}
      <label className="flex items-center gap-2 text-sm cursor-pointer" style={{ color: "var(--color-slate-300)" }}>
        <input
          type="checkbox"
          checked={filters.qualified_only}
          onChange={e => set("qualified_only", e.target.checked)}
          className="rounded accent-indigo-500"
        />
        Qualified only
      </label>
    </aside>
  );
}
