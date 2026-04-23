"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/dashboard", label: "Dashboard", icon: "⚡" },
  { href: "/proposals", label: "Proposals", icon: "📝" },
  { href: "/analytics", label: "Analytics", icon: "📊" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex min-h-screen bg-gray-950 text-white">
      <aside className="w-56 shrink-0 border-r border-gray-800 bg-gray-900 flex flex-col py-6 px-4 gap-2">
        <div className="mb-6 px-2">
          <span className="text-lg font-bold tracking-tight text-indigo-400">Proposal Intel</span>
        </div>
        {NAV.map(({ href, label, icon }) => (
          <Link
            key={href}
            href={href}
            className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              pathname.startsWith(href)
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:bg-gray-800 hover:text-white"
            }`}
          >
            <span>{icon}</span>
            {label}
          </Link>
        ))}
      </aside>
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
