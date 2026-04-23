"use client";
import { useEffect, useState } from "react";
import AppLayout from "@/components/layout";
import { useAuth } from "@/lib/hooks";
import { api } from "@/lib/api";

type User = { email: string; name?: string; bio?: string; hourly_rate?: number; tier: string };
type Profile = {
  headline?: string;
  skills?: string[];
  certifications?: string[];
  estimated_hours_per_project?: number;
};

export default function SettingsPage() {
  useAuth();
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    Promise.all([api.getMe(), api.getProfile().catch(() => null)]).then(([u, p]) => {
      setUser(u as User);
      if (p) setProfile(p as Profile);
    });
  }, []);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    try {
      await Promise.all([
        api.updateMe({
          name: user?.name,
          bio: user?.bio,
          hourly_rate: user?.hourly_rate,
        }),
        api.upsertProfile({
          headline: profile?.headline,
          skills: profile?.skills,
          certifications: profile?.certifications,
          estimated_hours_per_project: profile?.estimated_hours_per_project,
        }),
      ]);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } finally {
      setSaving(false);
    }
  }

  return (
    <AppLayout>
      <div className="min-h-screen p-6" style={{ background: "var(--color-dark)" }}>
        <h1 className="text-2xl font-bold text-white mb-8">Settings</h1>

        {!user ? (
          <div className="animate-pulse-slow text-slate-400 text-sm">Loading…</div>
        ) : (
          <form onSubmit={handleSave} className="max-w-2xl space-y-6">
            {/* Account section */}
            <Section title="Account">
              <Field label="Email">
                <input value={user.email} readOnly
                  className="w-full px-3 py-2 rounded-lg border text-sm opacity-60"
                  style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "var(--color-slate-300)" }} />
              </Field>
              <Field label="Plan">
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold capitalize"
                  style={{ background: "var(--color-indigo)", color: "white" }}>
                  {user.tier}
                </span>
              </Field>
              <Field label="Display name">
                <TextInput value={user.name ?? ""} onChange={v => setUser(u => u ? { ...u, name: v } : u)} />
              </Field>
              <Field label="Bio">
                <textarea
                  rows={3}
                  value={user.bio ?? ""}
                  onChange={e => setUser(u => u ? { ...u, bio: e.target.value } : u)}
                  placeholder="A short bio shown in your proposals…"
                  className="w-full px-3 py-2 rounded-lg border text-sm resize-none"
                  style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "white" }}
                />
              </Field>
              <Field label="Hourly rate (USD)">
                <input
                  type="number"
                  value={user.hourly_rate ?? ""}
                  onChange={e => setUser(u => u ? { ...u, hourly_rate: Number(e.target.value) } : u)}
                  placeholder="e.g. 75"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "white" }}
                />
              </Field>
            </Section>

            {/* Freelancer profile section */}
            <Section title="Freelancer profile">
              <p className="text-xs mb-4" style={{ color: "var(--color-slate-400)" }}>
                Used to personalise AI proposals. The more detail, the better.
              </p>
              <Field label="Headline">
                <TextInput
                  value={profile?.headline ?? ""}
                  onChange={v => setProfile(p => ({ ...(p ?? {}), headline: v }))}
                  placeholder="e.g. Senior Python developer & automation specialist"
                />
              </Field>
              <Field label="Skills (comma-separated)">
                <TextInput
                  value={profile?.skills?.join(", ") ?? ""}
                  onChange={v => setProfile(p => ({ ...(p ?? {}), skills: v.split(",").map(s => s.trim()).filter(Boolean) }))}
                  placeholder="Python, FastAPI, React, PostgreSQL…"
                />
              </Field>
              <Field label="Certifications (comma-separated)">
                <TextInput
                  value={profile?.certifications?.join(", ") ?? ""}
                  onChange={v => setProfile(p => ({ ...(p ?? {}), certifications: v.split(",").map(s => s.trim()).filter(Boolean) }))}
                  placeholder="AWS Solutions Architect, Google Analytics…"
                />
              </Field>
              <Field label="Estimated hours per project">
                <input
                  type="number"
                  value={profile?.estimated_hours_per_project ?? ""}
                  onChange={e => setProfile(p => ({ ...(p ?? {}), estimated_hours_per_project: Number(e.target.value) }))}
                  placeholder="e.g. 20"
                  className="w-full px-3 py-2 rounded-lg border text-sm"
                  style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "white" }}
                />
              </Field>
            </Section>

            {/* Save */}
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={saving}
                className="px-6 py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
                style={{ background: "var(--color-indigo)", color: "white" }}
              >
                {saving ? "Saving…" : "Save changes"}
              </button>
              {saved && <span className="text-sm text-green-400">Saved ✓</span>}
            </div>
          </form>
        )}
      </div>
    </AppLayout>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-xl p-6 border space-y-4"
      style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}>
      <h2 className="text-sm font-semibold text-white mb-2">{title}</h2>
      {children}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs mb-1" style={{ color: "var(--color-slate-400)" }}>{label}</label>
      {children}
    </div>
  );
}

function TextInput({ value, onChange, placeholder }: { value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <input
      type="text"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
      className="w-full px-3 py-2 rounded-lg border text-sm"
      style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "white" }}
    />
  );
}
