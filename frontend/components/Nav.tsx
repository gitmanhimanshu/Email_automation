"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import ThemeToggle from "./ThemeToggle";
import Logo from "./Logo";
import { AUTHOR, GITHUB_URL } from "@/lib/site";
import { cn } from "@/lib/cn";

const links = [
  { href: "/", label: "Home" },
  { href: "/pricing", label: "Pricing" },
  { href: "/docs", label: "Docs" },
  { href: "/docs/tools", label: "Tools" },
  { href: "/dashboard", label: "Dashboard" },
];

export default function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => setOpen(false), [pathname]);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 transition-shadow",
        scrolled && "shadow-[0_1px_0_var(--border)]"
      )}
    >
      <div className="glass border-b border-[var(--border)]">
        <nav className="mx-auto max-w-6xl px-6 h-14 flex items-center justify-between gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 font-semibold tracking-tight shrink-0"
          >
            <Logo size={26} />
            Setu
          </Link>

          <div className="hidden md:flex items-center gap-0.5 text-sm">
            {links.map((link) => {
              const active =
                link.href === "/docs"
                  ? pathname === "/docs"
                  : pathname.startsWith(link.href);
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={cn(
                    "px-3 py-1.5 rounded-md transition-colors",
                    active
                      ? "text-[var(--text-primary)] bg-[var(--surface-2)]"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  )}
                >
                  {link.label}
                </Link>
              );
            })}

            <span className="mx-1.5 h-4 w-px bg-[var(--border)]" aria-hidden="true" />

            <span className="flex items-center gap-1.5 px-2 py-1 rounded-md text-[var(--text-muted)] text-xs whitespace-nowrap">
              <span className="hidden lg:inline">built and maintained by</span>
              <span className="lg:hidden">by</span>
              <span className="font-semibold text-[var(--text-primary)]">{AUTHOR.name}</span>
            </span>
            <a
              href={AUTHOR.github}
              target="_blank"
              rel="noreferrer noopener"
              className="grid place-items-center w-7 h-7 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
              aria-label="Author GitHub"
            >
              <GithubMark />
            </a>
            <a
              href={AUTHOR.linkedin}
              target="_blank"
              rel="noreferrer noopener"
              className="grid place-items-center w-7 h-7 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
              aria-label="Author LinkedIn"
            >
              <LinkedInMark />
            </a>
          </div>

          <div className="flex items-center gap-2">
            <ThemeToggle />

            <Link
              href="/docs"
              className="hidden sm:inline-block text-sm px-3.5 py-1.5 rounded-full bg-[var(--text-primary)] text-[var(--plane)] font-medium hover:opacity-90 transition-opacity"
            >
              Get started
            </Link>
            <button
              onClick={() => setOpen((v) => !v)}
              className="md:hidden grid place-items-center w-8 h-8 rounded-md text-[var(--text-secondary)]"
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
            >
              {open ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </nav>

        {open && (
          <div className="md:hidden border-t border-[var(--border)] px-6 py-3 flex flex-col gap-1 text-sm">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-3 py-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--surface-2)]"
              >
                {link.label}
              </Link>
            ))}
            <div className="mt-2 pt-3 border-t border-[var(--border)] px-3 text-[var(--text-muted)] text-xs">
              built and maintained by <span className="font-semibold text-[var(--text-primary)]">{AUTHOR.name}</span>
            </div>
            <a
              href={AUTHOR.github}
              target="_blank"
              rel="noreferrer noopener"
              className="flex items-center gap-2 px-3 py-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--surface-2)]"
            >
              <GithubMark /> GitHub
            </a>
            <a
              href={AUTHOR.linkedin}
              target="_blank"
              rel="noreferrer noopener"
              className="flex items-center gap-2 px-3 py-2 rounded-md text-[var(--text-secondary)] hover:bg-[var(--surface-2)]"
            >
              <LinkedInMark /> LinkedIn
            </a>
          </div>
        )}
      </div>
    </header>
  );
}

function GithubMark() {
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

function LinkedInMark() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M3.6 5.6H.9V15h2.7V5.6zM2.24 1A1.55 1.55 0 100 2.55 1.55 1.55 0 002.24 1zM15 9.75c0-2.6-1.4-3.8-3.26-3.8a2.8 2.8 0 00-2.55 1.4V5.6H6.5V15h2.7V9.9c0-1.24.24-2.44 1.77-2.44s1.35 1.41 1.35 2.52V15H15V9.75z" />
    </svg>
  );
}
