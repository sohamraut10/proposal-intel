"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { logout } from "@/lib/auth";

const NAV = [
  { href: "/dashboard",  label: "Dashboard",  icon: "⚡" },
  { href: "/proposals",  label: "Proposals",  icon: "📝" },
  { href: "/analytics",  label: "Analytics",  icon: "📊" },
  { href: "/settings",   label: "Settings",   icon: "⚙️" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen" style={{ background: "var(--color-dark)" }}>
      {/* Sidebar */}
      <aside
        className="w-56 shrink-0 flex flex-col py-6 px-3 border-r"
        style={{ background: "var(--color-slate-900)", borderColor: "var(--color-slate-800)" }}
      >
        <div className="px-3 mb-8">
          <span
            className="text-lg tracking-tight"
            style={{ fontFamily: "Space Grotesk", fontWeight: 700, color: "var(--color-indigo)" }}
          >
            Proposal Intel
          </span>
        </div>

        <nav className="flex-1 flex flex-col gap-1">
          {NAV.map(({ href, label, icon }) => {
            const active = pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200"
                style={{
                  background: active ? "var(--color-indigo)" : "transparent",
                  color: active ? "var(--color-white)" : "var(--color-slate-400)",
                  fontWeight: active ? 500 : 400,
                }}
              >
                <span className="text-base">{icon}</span>
                {label}
              </Link>
            );
          })}
        </nav>

        <button
          onClick={logout}
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors mt-4"
          style={{ color: "var(--color-slate-400)" }}
        >
          <span>🚪</span>
          Sign out
        </button>
      </aside>

      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
