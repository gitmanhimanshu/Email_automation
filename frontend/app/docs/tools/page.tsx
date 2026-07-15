import type { Metadata } from "next";
import { AlertTriangle } from "lucide-react";
import DocsLayout from "@/components/DocsLayout";
import { CodeBlock } from "@/components/CodeWindow";
import { TOOLS } from "@/lib/site";

export const metadata: Metadata = {
  title: "Tools",
  description:
    "The six MCP tools Setu exposes: profile, resume link, address verification, single and batch sending, and history.",
};

export default function ToolsPage() {
  return (
    <DocsLayout>
      <article className="max-w-2xl">
        <h1 className="text-4xl font-semibold tracking-tight">Tools</h1>
        <p className="mt-4 text-lg text-[var(--text-secondary)] leading-relaxed">
          Setu exposes six tools. Your assistant decides when to call them — you
          never invoke these by hand.
        </p>

        <nav aria-label="On this page" className="mt-8 flex flex-wrap gap-2">
          {TOOLS.map((tool) => (
            <a
              key={tool.name}
              href={`#${tool.name}`}
              className="text-xs font-mono px-2.5 py-1.5 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
            >
              {tool.name}
            </a>
          ))}
        </nav>

        <div className="mt-12 space-y-14">
          {TOOLS.map((tool) => (
            <section key={tool.name} id={tool.name} className="scroll-mt-20">
              <div className="flex flex-wrap items-center gap-2.5">
                <h2 className="text-xl font-semibold tracking-tight font-mono">
                  {tool.name}
                </h2>
                {tool.destructive && (
                  <span
                    className="inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    style={{ background: "var(--accent-soft)", color: "var(--critical)" }}
                  >
                    <AlertTriangle size={9} />
                    irreversible
                  </span>
                )}
              </div>

              <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
                {tool.purpose}
              </p>

              <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Input
              </h3>
              {tool.input.length === 0 ? (
                <p className="mt-2 text-sm text-[var(--text-muted)]">None.</p>
              ) : (
                <div className="mt-2 scroll-x rounded-xl border border-[var(--border)]">
                  <table className="w-full text-sm border-collapse">
                    <thead>
                      <tr className="bg-[var(--surface-2)]">
                        <Th>Name</Th>
                        <Th>Type</Th>
                        <Th>Required</Th>
                        <Th>Description</Th>
                      </tr>
                    </thead>
                    <tbody>
                      {tool.input.map((param) => (
                        <tr key={param.name} className="border-b border-[var(--border)] last:border-0">
                          <td className="px-4 py-2.5 align-top">
                            <code className="text-xs whitespace-nowrap">{param.name}</code>
                          </td>
                          <td className="px-4 py-2.5 align-top">
                            <code className="text-xs text-[var(--accent)] whitespace-nowrap">
                              {param.type}
                            </code>
                          </td>
                          <td className="px-4 py-2.5 align-top text-xs text-[var(--text-muted)]">
                            {param.required ? "yes" : "no"}
                          </td>
                          <td className="px-4 py-2.5 align-top text-[var(--text-secondary)] text-xs">
                            {param.desc}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Returns
              </h3>
              <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                {tool.output}
              </p>

              <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
                Example
              </h3>
              <div className="mt-2">
                <CodeBlock lang="json" code={tool.example} />
              </div>
            </section>
          ))}
        </div>
      </article>
    </DocsLayout>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="text-left font-semibold px-4 py-2.5 border-b border-[var(--border)] whitespace-nowrap text-xs">
      {children}
    </th>
  );
}
