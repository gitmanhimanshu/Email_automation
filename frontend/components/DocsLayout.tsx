"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/cn";

const nav = [
  {
    title: "Getting started",
    items: [
      { href: "/docs", label: "Overview" },
      { href: "/docs#install", label: "Install" },
      { href: "/docs#resume", label: "Save your resume" },
      { href: "/docs#usage", label: "Using it" },
      { href: "/docs#limits", label: "Limits" },
      { href: "/docs#trouble", label: "Troubleshooting" },
    ],
  },
  {
    title: "Reference",
    items: [
      { href: "/docs/tools", label: "Tools" },
      { href: "/docs/api", label: "HTTP API" },
    ],
  },
  {
    title: "More",
    items: [
      { href: "/#security", label: "Security" },
      { href: "/#faq", label: "FAQ" },
    ],
  },
];

export default function DocsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="mx-auto max-w-6xl px-6 grid lg:grid-cols-[200px_1fr] gap-10 lg:gap-14 py-12">
      <aside className="lg:sticky lg:top-20 lg:self-start lg:max-h-[calc(100vh-6rem)] lg:overflow-y-auto">
        <nav className="space-y-6">
          {nav.map((group) => (
            <div key={group.title}>
              <h2 className="text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                {group.title}
              </h2>
              <ul className="mt-2.5 space-y-0.5">
                {group.items.map((item) => {
                  const active = pathname === item.href && !item.href.includes("#");
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        className={cn(
                          "block px-2.5 py-1.5 -ml-2.5 rounded-md text-sm transition-colors",
                          active
                            ? "text-[var(--text-primary)] bg-[var(--surface-2)] font-medium"
                            : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                        )}
                      >
                        {item.label}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
      </aside>

      <div className="min-w-0">{children}</div>
    </div>
  );
}
