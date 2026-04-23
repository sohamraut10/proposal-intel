"use client";
import { useState } from "react";
import AppLayout from "@/components/layout";
import { useAuth, useProposals } from "@/lib/hooks";
import { api } from "@/lib/api";
import { statusBadge, formatCurrency, cn } from "@/lib/utils";

const STATUS_TABS = ["all", "pending", "submitted", "won", "lost"];

type Proposal = {
  id: string;
  job_id: string;
  platform?: string;
  proposal_text: string;
  cover_letter?: string;
  approach?: string;
  highlighted_strengths?: string[];
  bid_amount?: number;
  currency: string;
  strategy: string;
  status: string;
  quality_score?: number;
  win_probability?: number;
  estimated_response_time?: string;
  tokens_used: number;
  model_used?: string;
  created_at: string;
};

export default function ProposalsPage() {
  useAuth();
  const [tab, setTab] = useState("all");
  const { proposals, loading, reload } = useProposals(tab === "all" ? undefined : tab);
  const [selected, setSelected] = useState<Proposal | null>(null);
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState("");
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState(false);

  async function handleStatusChange(id: string, status: string) {
    await api.updateProposal(id, { status });
    await reload();
    if (selected?.id === id) setSelected(s => s ? { ...s, status } : s);
  }

  async function handleOutcome(id: string, status: "won" | "lost") {
    const amount = status === "won" ? Number(prompt("Actual amount won ($)?") || 0) : undefined;
    await api.recordOutcome(id, status, amount || undefined);
    await reload();
    if (selected?.id === id) setSelected(s => s ? { ...s, status } : s);
  }

  async function handleSave() {
    if (!selected) return;
    setSaving(true);
    try {
      await api.updateProposal(selected.id, { proposal_text: editText });
      setSelected({ ...selected, proposal_text: editText });
      setEditing(false);
      await reload();
    } finally {
      setSaving(false);
    }
  }

  function handleCopy() {
    if (!selected) return;
    navigator.clipboard.writeText(selected.proposal_text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <AppLayout>
      <div className="flex h-screen overflow-hidden" style={{ background: "#f8fafc", color: "#0f172a" }}>
        {/* Sidebar */}
        <aside className="w-72 shrink-0 flex flex-col border-r border-gray-200 bg-white overflow-hidden">
          {/* Tabs */}
          <div className="flex gap-1 p-3 border-b border-gray-100 flex-wrap">
            {STATUS_TABS.map(s => (
              <button
                key={s}
                onClick={() => setTab(s)}
                className={cn(
                  "px-3 py-1 rounded-full text-xs capitalize transition-colors",
                  tab === s
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                )}
              >
                {s}
              </button>
            ))}
          </div>

          {/* List */}
          <div className="flex-1 overflow-y-auto divide-y divide-gray-50">
            {loading ? (
              <div className="text-center py-12 text-sm text-gray-400">Loading…</div>
            ) : proposals.length === 0 ? (
              <div className="text-center py-12 text-sm text-gray-400">No proposals yet</div>
            ) : (
              (proposals as Proposal[]).map(p => (
                <button
                  key={p.id}
                  onClick={() => { setSelected(p); setEditing(false); setEditText(p.proposal_text); }}
                  className={cn(
                    "w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors",
                    selected?.id === p.id && "bg-blue-50 border-l-2 border-blue-500"
                  )}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className={cn("text-xs px-2 py-0.5 rounded-full border", statusBadge(p.status))}>
                      {p.status}
                    </span>
                    {p.bid_amount && (
                      <span className="text-xs text-gray-500 font-mono">{formatCurrency(p.bid_amount)}</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{p.proposal_text.slice(0, 100)}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {p.platform && `${p.platform} · `}{new Date(p.created_at).toLocaleDateString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* Detail */}
        <div className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              Select a proposal
            </div>
          ) : (
            <div className="max-w-2xl mx-auto">
              {/* 3 metric cards */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                {[
                  { label: "Win probability", value: selected.win_probability ? `${Math.round(selected.win_probability * 100)}%` : "—", color: "text-blue-600" },
                  { label: "Quality score", value: selected.quality_score ? `${selected.quality_score}/100` : "—", color: "text-green-600" },
                  { label: "Response time", value: selected.estimated_response_time ?? "—", color: "text-purple-600" },
                ].map(({ label, value, color }) => (
                  <div key={label} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 text-center">
                    <p className="text-xs text-gray-500 mb-1">{label}</p>
                    <p className={cn("text-xl font-bold font-mono", color)}>{value}</p>
                  </div>
                ))}
              </div>

              {/* Actions */}
              <div className="flex gap-2 mb-5 flex-wrap">
                <select
                  value={selected.status}
                  onChange={e => handleStatusChange(selected.id, e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
                >
                  {["pending", "submitted", "won", "lost"].map(s => (
                    <option key={s} value={s}>{s}</option>
                  ))}
                </select>

                {selected.status === "submitted" && (
                  <>
                    <button onClick={() => handleOutcome(selected.id, "won")}
                      className="px-3 py-1.5 rounded-lg text-sm bg-green-600 text-white">
                      Mark Won
                    </button>
                    <button onClick={() => handleOutcome(selected.id, "lost")}
                      className="px-3 py-1.5 rounded-lg text-sm bg-red-600 text-white">
                      Mark Lost
                    </button>
                  </>
                )}

                <button onClick={handleCopy}
                  className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 hover:bg-gray-100">
                  {copied ? "Copied!" : "Copy"}
                </button>
                <button onClick={() => { setEditing(!editing); setEditText(selected.proposal_text); }}
                  className="px-3 py-1.5 rounded-lg text-sm border border-gray-300 hover:bg-gray-100">
                  {editing ? "Cancel" : "Edit"}
                </button>

                <span className="ml-auto text-xs text-gray-400 self-center">
                  {selected.model_used} · {selected.tokens_used} tokens · {selected.strategy}
                </span>
              </div>

              {/* Cover letter */}
              {selected.cover_letter && (
                <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4">
                  <p className="text-xs font-semibold text-blue-600 mb-1">Cover letter</p>
                  <p className="text-sm text-blue-900">{selected.cover_letter}</p>
                </div>
              )}

              {/* Strengths */}
              {selected.highlighted_strengths && selected.highlighted_strengths.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-4">
                  {selected.highlighted_strengths.map((s, i) => (
                    <span key={i} className="text-xs px-2 py-1 bg-green-50 text-green-700 border border-green-100 rounded-full">
                      {s}
                    </span>
                  ))}
                </div>
              )}

              {/* Proposal text */}
              {editing ? (
                <div>
                  <textarea
                    value={editText}
                    onChange={e => setEditText(e.target.value)}
                    className="w-full h-80 border border-gray-300 rounded-xl p-4 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                    style={{ fontFamily: "Inter" }}
                  />
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50"
                  >
                    {saving ? "Saving…" : "Save"}
                  </button>
                </div>
              ) : (
                <div className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed"
                  style={{ fontFamily: "Inter" }}>
                  {selected.proposal_text}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
