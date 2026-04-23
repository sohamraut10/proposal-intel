"use client";
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await api.login(email, password);
      setToken(access_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      setError((err as Error).message ?? "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
      style={{ background: "var(--color-dark)" }}>
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <span className="text-2xl font-bold text-white">Proposal Intel</span>
          <p className="text-sm mt-1" style={{ color: "var(--color-slate-400)" }}>Sign in to your account</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl p-8 border space-y-4"
          style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}>
          {error && (
            <div className="rounded-lg px-4 py-3 text-sm border"
              style={{ background: "#7f1d1d40", borderColor: "#991b1b60", color: "#fca5a5" }}>
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm mb-1.5" style={{ color: "var(--color-slate-300)" }}>Email</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              placeholder="you@example.com"
              className="w-full rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "white", border: "1px solid var(--color-slate-700)" }}
            />
          </div>

          <div>
            <label className="block text-sm mb-1.5" style={{ color: "var(--color-slate-300)" }}>Password</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="••••••••"
              className="w-full rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              style={{ background: "var(--color-slate-800)", borderColor: "var(--color-slate-700)", color: "white", border: "1px solid var(--color-slate-700)" }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
            style={{ background: "var(--color-indigo)", color: "white" }}
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-center text-sm" style={{ color: "var(--color-slate-400)" }}>
            No account?{" "}
            <Link href="/auth/signup" className="hover:underline" style={{ color: "#818cf8" }}>
              Register
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
