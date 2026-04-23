"use client";
import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { getToken, logout } from "./auth";
import { api } from "./api";

export function useAuth() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/auth/login");
  }, [router]);

  return { logout };
}

export function useJobs(params?: Record<string, string | number | boolean>) {
  const [jobs, setJobs] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listJobs(params);
      setJobs(data);
    } catch (e: unknown) {
      const msg = (e as Error).message;
      if (msg.includes("401")) logout();
      else setError(msg);
    } finally {
      setLoading(false);
    }
  }, [JSON.stringify(params)]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { load(); }, [load]);
  return { jobs, loading, error, reload: load };
}

export function useProposals(status?: string) {
  const [proposals, setProposals] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.listProposals(status);
      setProposals(data);
    } catch (e: unknown) {
      if ((e as Error).message?.includes("401")) logout();
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => { load(); }, [load]);
  return { proposals, loading, reload: load };
}

export function useAnalytics(periodDays = 30) {
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [winRates, setWinRates] = useState<Record<string, unknown>[]>([]);
  const [categoryRates, setCategoryRates] = useState<Record<string, unknown>[]>([]);
  const [bidDist, setBidDist] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getSummary(periodDays),
      api.getWinRates(),
      api.getCategoryRates(),
      api.getBidDistribution(),
    ])
      .then(([s, w, c, b]) => {
        setSummary(s as Record<string, unknown>);
        setWinRates(w as Record<string, unknown>[]);
        setCategoryRates(c as Record<string, unknown>[]);
        setBidDist(b as Record<string, unknown>[]);
      })
      .catch((e: unknown) => { if ((e as Error).message?.includes("401")) logout(); })
      .finally(() => setLoading(false));
  }, [periodDays]);

  return { summary, winRates, categoryRates, bidDist, loading };
}
