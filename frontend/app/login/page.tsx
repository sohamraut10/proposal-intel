"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OldLoginRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/auth/login"); }, [router]);
  return null;
}
