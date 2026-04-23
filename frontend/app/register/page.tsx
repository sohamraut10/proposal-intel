"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function OldRegisterRedirect() {
  const router = useRouter();
  useEffect(() => { router.replace("/auth/signup"); }, [router]);
  return null;
}
