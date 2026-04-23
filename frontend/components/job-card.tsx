import { formatBudget, formatRelativeTime, scoreBg, cn } from "@/lib/utils";

type Job = {
  id: string;
  platform: string;
  title: string;
  description?: string | null;
  category?: string | null;
  budget_min?: number | null;
  budget_max?: number | null;
  budget_type?: string | null;
  client_name?: string | null;
  client_rating?: number | null;
  client_jobs_posted?: number | null;
  proposals_count?: number;
  score_total: number;
  win_probability?: number | null;
  is_qualified: boolean;
  posted_at?: string | null;
  url?: string | null;
};

const PLATFORM_COLORS: Record<string, string> = {
  upwork:     "bg-green-500/20 text-green-400 border-green-500/30",
  freelancer: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  pph:        "bg-orange-500/20 text-orange-400 border-orange-500/30",
};

type Props = {
  job: Job;
  selected?: boolean;
  index?: number;
  onClick: () => void;
};

export default function JobCard({ job, selected, index = 0, onClick }: Props) {
  const stagger = Math.min(index + 1, 5);
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left p-4 rounded-xl border transition-all duration-200 animate-fade-in",
        `card-stagger-${stagger}`,
        selected
          ? "border-indigo-500 bg-indigo-500/10 scale-[1.01]"
          : "border-slate-800 bg-slate-900 hover:border-slate-600 hover:scale-[1.01]"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Badges */}
          <div className="flex flex-wrap items-center gap-1.5 mb-1.5">
            <span className={cn("text-xs px-2 py-0.5 rounded-full border", PLATFORM_COLORS[job.platform] ?? "bg-slate-700 text-slate-300 border-slate-600")}>
              {job.platform}
            </span>
            {job.is_qualified && (
              <span className="text-xs px-2 py-0.5 rounded-full border bg-green-500/20 text-green-400 border-green-500/30">
                Qualified
              </span>
            )}
            {job.category && (
              <span className="text-xs text-slate-500">{job.category}</span>
            )}
          </div>

          {/* Title */}
          <h3 className="text-sm font-semibold text-white truncate">{job.title}</h3>

          {/* Description snippet */}
          {job.description && (
            <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
              {job.description}
            </p>
          )}

          {/* Meta row */}
          <div className="flex flex-wrap gap-3 mt-2 text-xs" style={{ color: "var(--color-slate-400)", fontFamily: "Fira Code" }}>
            <span>{formatBudget(job.budget_min, job.budget_max)}</span>
            {job.client_rating && <span>⭐ {job.client_rating.toFixed(1)}</span>}
            {job.proposals_count != null && <span>{job.proposals_count} bids</span>}
            {job.posted_at && <span>{formatRelativeTime(job.posted_at)}</span>}
          </div>
        </div>

        {/* Score */}
        <div className="flex flex-col items-center shrink-0 gap-1">
          <span className={cn("text-xl font-bold tabular-nums", scoreBg(job.score_total), "px-2 py-0.5 rounded-lg border text-sm")}>
            {Math.round(job.score_total)}
          </span>
          <span className="text-xs text-slate-500">score</span>
        </div>
      </div>
    </button>
  );
}

export type { Job };
