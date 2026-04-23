"use client";
import { useEffect, useState } from "react";
import AppLayout from "@/components/layout";
import { api } from "@/lib/api";

type Proposal = {
  id: string;
  job_id: string;
  content: string;
  cover_letter: string | null;
  bid_amount: number | null;
  bid_type: string | null;
  status: string;
  tokens_used: number;
  model_used: string | null;
  created_at: string;
};

const STATUS_OPTIONS = ["draft", "submitted", "interview", "won", "lost"];
const STATUS_COLORS: Record<string, string> = {
  draft: "bg-gray-200 text-gray-800",
  submitted: "bg-blue-100 text-blue-800",
  interview: "bg-yellow-100 text-yellow-800",
  won: "bg-green-100 text-green-800",
  lost: "bg-red-100 text-red-800",
};

export default function ProposalsPage() {
  const [proposals, setProposals] = useState<Proposal[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterStatus, setFilterStatus] = useState("");
  const [selected, setSelected] = useState<Proposal | null>(null);
  const [editing, setEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const data = await api.listProposals(filterStatus || undefined);
      setProposals(data as Proposal[]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [filterStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  function openProposal(p: Proposal) {
    setSelected(p);
    setEditing(false);
    setEditContent(p.content);
  }

  async function handleStatusChange(proposalId: string, status: string) {
    await api.updateProposal(proposalId, { status });
    await load();
    if (selected?.id === proposalId) setSelected((s) => s ? { ...s, status } : s);
  }

  async function handleSaveEdit() {
    if (!selected) return;
    setSaving(true);
    try {
      await api.updateProposal(selected.id, { content: editContent });
      setSelected({ ...selected, content: editContent });
      setEditing(false);
      await load();
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppLayout>
      <div className="flex h-screen bg-white text-gray-900">
        {/* List */}
        <div className="w-80 shrink-0 border-r border-gray-200 flex flex-col bg-gray-50">
          <div className="p-4 border-b border-gray-200">
            <h1 className="text-lg font-semibold mb-3">Proposals</h1>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
            >
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          <div className="flex-1 overflow-y-auto">
            {loading ? (
              <div className="text-gray-400 text-center py-12 text-sm">Loading…</div>
            ) : proposals.length === 0 ? (
              <div className="text-gray-400 text-center py-12 text-sm">No proposals yet</div>
            ) : (
              proposals.map((p) => (
                <button
                  key={p.id}
                  onClick={() => openProposal(p)}
                  className={`w-full text-left p-4 border-b border-gray-100 hover:bg-white transition-colors ${
                    selected?.id === p.id ? "bg-white border-l-2 border-l-indigo-500" : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                        STATUS_COLORS[p.status] ?? "bg-gray-100 text-gray-600"
                      }`}
                    >
                      {p.status}
                    </span>
                    {p.bid_amount && (
                      <span className="text-xs text-gray-500">${p.bid_amount}</span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">{p.content.slice(0, 120)}</p>
                  <p className="text-xs text-gray-400 mt-1">
                    {new Date(p.created_at).toLocaleDateString()}
                  </p>
                </button>
              ))
            )}
          </div>
        </div>

        {/* Detail */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selected ? (
            <div className="flex items-center justify-center h-full text-gray-400">
              Select a proposal to view
            </div>
          ) : (
            <div className="max-w-2xl mx-auto">
              <div className="flex items-center justify-between mb-4">
                <div className="flex gap-2">
                  <select
                    value={selected.status}
                    onChange={(e) => handleStatusChange(selected.id, e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm"
                  >
                    {STATUS_OPTIONS.map((s) => (
                      <option key={s} value={s}>{s}</option>
                    ))}
                  </select>
                  <span className="text-sm text-gray-400 self-center">
                    {selected.model_used} · {selected.tokens_used} tokens
                  </span>
                </div>
                <button
                  onClick={() => setEditing(!editing)}
                  className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50"
                >
                  {editing ? "Cancel" : "Edit"}
                </button>
              </div>

              {selected.cover_letter && (
                <div className="bg-indigo-50 border border-indigo-100 rounded-xl p-4 mb-4">
                  <p className="text-xs font-semibold text-indigo-600 mb-1">Cover letter</p>
                  <p className="text-sm text-indigo-900">{selected.cover_letter}</p>
                </div>
              )}

              {editing ? (
                <div>
                  <textarea
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="w-full h-96 border border-gray-300 rounded-xl p-4 text-sm font-mono resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                  <button
                    onClick={handleSaveEdit}
                    disabled={saving}
                    className="mt-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm disabled:opacity-50"
                  >
                    {saving ? "Saving…" : "Save changes"}
                  </button>
                </div>
              ) : (
                <div className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed">
                  {selected.content}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
}
