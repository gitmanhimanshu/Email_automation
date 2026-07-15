import Link from "next/link";
import Logo from "./Logo";
import { AUTHOR, CONTACT_EMAIL, GITHUB_URL, MIMANASA, TAGLINE } from "@/lib/site";

/* Only routes that actually exist. A dead link in a footer is the fastest way to
   look unfinished — add entries here as the pages land, not before. */
const columns = [
  {
    title: "Product",
    links: [
      { href: "/docs", label: "Documentation" },
      { href: "/docs#install", label: "Installation" },
      { href: "/docs/tools", label: "Tools" },
      { href: "/docs/api", label: "API reference" },
      { href: "/dashboard", label: "Dashboard" },
    ],
  },
  {
    title: "Learn",
    links: [
      { href: "/#what-is-mcp", label: "What is MCP?" },
      { href: "/#how", label: "How it works" },
      { href: "/#security", label: "Security" },
      { href: "/#faq", label: "FAQ" },
    ],
  },
];

const external = [
  { href: MIMANASA.site, label: MIMANASA.name },
  { href: MIMANASA.edu, label: `${MIMANASA.name} Edu` },
];

export default function Footer() {
  return (
    <footer className="border-t border-[var(--border)] mt-28">
      <div className="mx-auto max-w-6xl px-6 py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <div className="flex items-center gap-2 font-semibold tracking-tight">
              <Logo size={28} />
              Setu
            </div>
            <p lang="hi" className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-xs">
              {TAGLINE.hi}
            </p>
            <p className="mt-2 text-xs text-[var(--text-muted)] max-w-xs leading-relaxed">
              {TAGLINE.en}
            </p>

            <div className="mt-6">
              <p className="text-xs text-[var(--text-muted)]">{AUTHOR.role}</p>
              <p className="mt-1 text-sm font-medium">{AUTHOR.name}</p>
              <div className="mt-3 flex items-center gap-2">
                <a
                  href={AUTHOR.github}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
                >
                  <GithubMark />
                  GitHub
                </a>
                <a
                  href={AUTHOR.linkedin}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
                >
                  <LinkedInMark />
                  LinkedIn
                </a>
              </div>
            </div>
          </div>

          {columns.map((col) => (
            <div key={col.title}>
              <h2 className="text-sm font-semibold">{col.title}</h2>
              <ul className="mt-3 space-y-2 text-sm">
                {col.links.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                    >
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}

          <div>
            <h2 className="text-sm font-semibold">Elsewhere</h2>
            <ul className="mt-3 space-y-2 text-sm">
              {external.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    target="_blank"
                    rel="noreferrer noopener"
                    className="inline-flex items-center gap-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                  >
                    {link.label}
                    <ArrowOut />
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-6 border-t border-[var(--border)] flex flex-wrap items-center justify-between gap-4 text-xs text-[var(--text-muted)]">
          <p className="max-w-lg">
            Send-only Gmail access. Setu can never read your inbox — that is a
            permission it does not have, not a promise it makes.
          </p>
          <div className="flex items-center gap-4">

            <a
              href={`mailto:${CONTACT_EMAIL}`}
              className="hover:text-[var(--text-secondary)] transition-colors"
            >
              Contact
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function GithubMark() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0016 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

/* Brand marks are hand-rolled: lucide-react v1 dropped its brand icons, so
   importing them is not an option. */
function LinkedInMark() {
  return (
    <svg width="13" height="13" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M3.6 5.6H.9V15h2.7V5.6zM2.24 1A1.55 1.55 0 100 2.55 1.55 1.55 0 002.24 1zM15 9.75c0-2.6-1.4-3.8-3.26-3.8a2.8 2.8 0 00-2.55 1.4V5.6H6.5V15h2.7V9.9c0-1.24.24-2.44 1.77-2.44s1.35 1.41 1.35 2.52V15H15V9.75z" />
    </svg>
  );
}

function ArrowOut() {
  return (
    <svg width="10" height="10" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path
        d="M3.5 8.5L8.5 3.5M8.5 3.5H4.5M8.5 3.5V7.5"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
