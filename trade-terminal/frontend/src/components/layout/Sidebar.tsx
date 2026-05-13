"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart2, Bot, BrainCircuit, Settings, TrendingUp } from "lucide-react";

const NAV = [
  { href: "/", icon: TrendingUp, label: "Dashboard" },
  { href: "/bots", icon: Bot, label: "Bots" },
  { href: "/analysis", icon: BrainCircuit, label: "AI Analiz" },
  { href: "/settings", icon: Settings, label: "Ayarlar" },
];

export default function Sidebar() {
  const path = usePathname();

  return (
    <aside className="w-14 flex flex-col items-center py-4 bg-bg-secondary border-r border-bg-border gap-1 shrink-0">
      <div className="mb-4 text-accent-blue">
        <BarChart2 size={22} />
      </div>
      {NAV.map(({ href, icon: Icon, label }) => {
        const active = href === "/" ? path === "/" : path.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            title={label}
            className={`w-10 h-10 flex items-center justify-center rounded-md transition-colors ${
              active
                ? "bg-accent-blue/20 text-accent-blue"
                : "text-text-muted hover:text-text-secondary hover:bg-bg-tertiary"
            }`}
          >
            <Icon size={18} />
          </Link>
        );
      })}
    </aside>
  );
}
