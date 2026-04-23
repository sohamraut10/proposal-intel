export function cn(...classes: (string | undefined | false | null)[]): string {
  return classes.filter(Boolean).join(" ");
}

export function formatCurrency(amount: number | null | undefined, currency = "USD"): string {
  if (amount == null) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
}

export function formatBudget(min?: number | null, max?: number | null): string {
  if (!min && !max) return "Budget TBD";
  if (min && max && min !== max) return `${formatCurrency(min)}–${formatCurrency(max)}`;
  return formatCurrency(min ?? max);
}

export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return "Unknown";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export function scoreColor(score: number): string {
  if (score >= 80) return "text-green-400";
  if (score >= 60) return "text-yellow-400";
  return "text-red-400";
}

export function scoreBg(score: number): string {
  if (score >= 80) return "bg-green-500/20 text-green-400 border-green-500/30";
  if (score >= 60) return "bg-yellow-500/20 text-yellow-400 border-yellow-500/30";
  return "bg-red-500/20 text-red-400 border-red-500/30";
}

export function statusBadge(status: string): string {
  const map: Record<string, string> = {
    pending:   "bg-yellow-500/20 text-yellow-300 border-yellow-500/30",
    submitted: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    won:       "bg-green-500/20 text-green-300 border-green-500/30",
    lost:      "bg-red-500/20 text-red-300 border-red-500/30",
    draft:     "bg-slate-500/20 text-slate-300 border-slate-500/30",
  };
  return map[status] ?? map.draft;
}

export function tierLabel(tier: string): string {
  return { free: "Free", pro: "Pro", agency: "Agency", enterprise: "Enterprise" }[tier] ?? tier;
}
