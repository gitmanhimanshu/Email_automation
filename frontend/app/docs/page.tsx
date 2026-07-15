import type { Metadata } from "next";
import Link from "next/link";
import { AlertTriangle, ArrowRight } from "lucide-react";
import DocsLayout from "@/components/DocsLayout";
import { CodeBlock, CopyButton } from "@/components/CodeWindow";
import { LIMITS, MCP_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "Documentation",
  description:
    "Connect Setu to Claude, ChatGPT, or any MCP client. One URL, one Google sign-in — no install.",
};

export default function Docs() {
  return (
    <DocsLayout>
      <article className="max-w-2xl">
        <h1 className="text-4xl font-semibold tracking-tight">Documentation</h1>
        <p className="mt-4 text-lg text-[var(--text-secondary)] leading-relaxed">
          Setu is a hosted MCP server. There is nothing to install and no config
          file to edit — you add one URL to your assistant and sign in with
          Google.
        </p>

        {/* Install */}
        <section id="install" className="mt-14 scroll-mt-20">
          <h2 className="text-2xl font-semibold tracking-tight">Install</h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            Everything starts from one URL. The <Code>/mcp</Code> on the end
            matters — without it the client won&apos;t find the server.
          </p>

          <div className="mt-5 rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4">
            <div className="flex items-center justify-between gap-3 mb-2">
              <span className="text-xs font-medium text-[var(--text-muted)]">
                Connector URL
              </span>
              <CopyButton value={MCP_URL} />
            </div>
            <code className="block text-sm scroll-x whitespace-nowrap">{MCP_URL}</code>
          </div>

          <H3>Claude</H3>
          <Steps
            items={[
              <>Settings → <B>Connectors</B> → <B>Add custom connector</B></>,
              <>Paste the URL, click <B>Connect</B></>,
              <>Sign in with Google when the popup opens</>,
            ]}
          />

          <H3>ChatGPT</H3>
          <Note>
            Custom connectors require <B>Developer mode</B> and a paid plan
            (Plus, Pro, Team, or Enterprise). They aren&apos;t available on the
            free tier.
          </Note>
          <Steps
            items={[
              <>Settings → Connectors → <B>Advanced</B> → enable <B>Developer mode</B></>,
              <>Settings → Connectors → <B>Create</B></>,
              <>Name it <Code>Setu</Code>, paste the URL, set auth to <B>OAuth</B></>,
              <>Click <B>Create</B> → sign in with Google</>,
            ]}
          />

          <H3>Claude Code</H3>
          <div className="mt-3">
            <CodeBlock
              lang="bash"
              code={`claude mcp add --transport http setu ${MCP_URL}`}
            />
          </div>

          <H3>Cursor, VS Code, Windsurf, Cline</H3>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            These clients accept a remote MCP server with OAuth; add the same URL
            wherever the client asks for one. We haven&apos;t verified each of
            them ourselves, so if one misbehaves, please open an issue — that is
            useful to us.
          </p>
        </section>

        {/* The warning */}
        <section className="mt-14">
          <div className="rounded-xl border border-[var(--border)] border-l-2 border-l-[var(--warning)] bg-[var(--surface)] p-6">
            <div className="flex items-start gap-3">
              <AlertTriangle size={17} className="mt-0.5 shrink-0" style={{ color: "var(--warning)" }} />
              <div>
                <h2 className="font-semibold">
                  Google will call this app unverified
                </h2>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed">
                  You&apos;ll see <em>“Google hasn&apos;t verified this app”</em>.
                  Click <B>Advanced</B> → <B>Go to Setu (unsafe)</B>.
                </p>
                <p className="mt-3 text-sm text-[var(--text-secondary)] leading-relaxed">
                  “Unsafe” is Google&apos;s wording for “hasn&apos;t finished our
                  review”, not a finding about Setu. The screen after it is the
                  one that actually matters — it lists exactly one permission:{" "}
                  <B>Send email on your behalf</B>. That is the whole of what
                  Setu can do to your account.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Resume */}
        <section id="resume" className="mt-14 scroll-mt-20">
          <h2 className="text-2xl font-semibold tracking-tight">
            Save your resume
          </h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            Setu appends your resume link to every application, so save it once
            before sending. Ask your assistant:
          </p>
          <div className="mt-4">
            <CodeBlock
              lang="prompt"
              code={`Save my resume link: https://drive.google.com/file/d/…/view`}
            />
          </div>
          <Note>
            Share the file as <B>“Anyone with the link”</B> first. Setu fetches
            the URL to check, and rejects a private link — otherwise HR clicks it,
            sees “Request access”, and you never learn the application went
            nowhere.
          </Note>
        </section>

        {/* Usage */}
        <section id="usage" className="mt-14 scroll-mt-20">
          <h2 className="text-2xl font-semibold tracking-tight">Using it</h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            Setu doesn&apos;t write anything — your assistant does. Give it the
            context a good application needs and it will do the research itself.
          </p>
          <div className="mt-4">
            <CodeBlock
              lang="prompt"
              code={`Find fintech startups in Bangalore hiring backend engineers.
For each one, find their careers email and draft an
application using my resume. Show me the list and one full
draft before you send anything.`}
            />
          </div>
          <p className="mt-4 text-[var(--text-secondary)] leading-relaxed">
            Asking to see a draft first is worth the extra turn. The assistant is
            writing as you, to someone who may decide whether to interview you.
          </p>
        </section>

        {/* Limits */}
        <section id="limits" className="mt-14 scroll-mt-20">
          <h2 className="text-2xl font-semibold tracking-tight">Limits</h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            These are enforced by the server, not suggested to the model.
          </p>
          <div className="mt-5 scroll-x rounded-xl border border-[var(--border)]">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-[var(--surface-2)]">
                  <Th>Limit</Th>
                  <Th>Value</Th>
                  <Th>Why</Th>
                </tr>
              </thead>
              <tbody>
                <Row
                  cells={[
                    "Per day",
                    `${LIMITS.perDay}`,
                    "Gmail's ceiling is higher, but staying under it protects your sending reputation",
                  ]}
                />
                <Row
                  cells={[
                    "Per batch",
                    `${LIMITS.perBatch}`,
                    "Small enough that you review as you go",
                  ]}
                />
                <Row
                  cells={[
                    "Delay",
                    `${LIMITS.defaultDelaySeconds}s`,
                    "A burst is a pattern Gmail reads as automation",
                  ]}
                />
                <Row
                  cells={[
                    "Resume",
                    "required",
                    "An application with no resume wastes the contact",
                  ]}
                />
                <Row
                  cells={["Duplicates", "blocked", "Every send is recorded, across sessions"]}
                />
              </tbody>
            </table>
          </div>
        </section>

        {/* Trouble */}
        <section id="trouble" className="mt-14 scroll-mt-20">
          <h2 className="text-2xl font-semibold tracking-tight">
            Troubleshooting
          </h2>
          <dl className="mt-5 space-y-5">
            <Trouble q="The client can't connect">
              Check the URL ends in <Code>/mcp</Code>. That&apos;s the usual one.
            </Trouble>
            <Trouble q="“Google hasn't verified this app”">
              Expected. Advanced → Go to Setu. See the note above.
            </Trouble>
            <Trouble q="My resume link was rejected">
              It isn&apos;t public. Drive → Share → “Anyone with the link” →
              Viewer.
            </Trouble>
            <Trouble q="It refuses to send">
              Either no resume link is saved, or today&apos;s {LIMITS.perDay} are
              spent. Ask your assistant to check your profile.
            </Trouble>
            <Trouble q="I want to revoke access">
              <a
                href="https://myaccount.google.com/permissions"
                target="_blank"
                rel="noreferrer noopener"
                className="text-[var(--accent)] hover:underline"
              >
                myaccount.google.com/permissions
              </a>{" "}
              → find Setu → remove. Immediate, and you don&apos;t need to ask us.
            </Trouble>
          </dl>
        </section>

        <div className="mt-14 flex flex-wrap gap-3">
          <Link
            href="/docs/tools"
            className="group inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-sm font-medium hover:border-[var(--border-strong)] transition-colors"
          >
            Tool reference
            <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            href="/docs/api"
            className="group inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-sm font-medium hover:border-[var(--border-strong)] transition-colors"
          >
            HTTP API
            <ArrowRight size={14} className="group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </article>
    </DocsLayout>
  );
}

function H3({ children }: { children: React.ReactNode }) {
  return <h3 className="mt-8 font-semibold">{children}</h3>;
}

function Steps({ items }: { items: React.ReactNode[] }) {
  return (
    <ol className="mt-3 space-y-2.5">
      {items.map((item, i) => (
        <li key={i} className="flex gap-3 text-sm">
          <span className="shrink-0 grid place-items-center w-5 h-5 rounded-full bg-[var(--surface-2)] border border-[var(--border)] text-xs font-semibold tabular text-[var(--text-secondary)]">
            {i + 1}
          </span>
          <span className="text-[var(--text-secondary)] pt-0.5">{item}</span>
        </li>
      ))}
    </ol>
  );
}

function Note({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text-secondary)] leading-relaxed">
      {children}
    </p>
  );
}

function Trouble({ q, children }: { q: string; children: React.ReactNode }) {
  return (
    <div>
      <dt className="font-medium text-sm">{q}</dt>
      <dd className="mt-1 text-sm text-[var(--text-secondary)] leading-relaxed">
        {children}
      </dd>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="text-left font-semibold px-4 py-2.5 border-b border-[var(--border)] whitespace-nowrap">
      {children}
    </th>
  );
}

function Row({ cells }: { cells: string[] }) {
  return (
    <tr className="border-b border-[var(--border)] last:border-0">
      {cells.map((cell, i) => (
        <td
          key={i}
          className={`px-4 py-2.5 align-top ${
            i === 0 ? "font-medium whitespace-nowrap" : "text-[var(--text-secondary)]"
          } ${i === 1 ? "tabular" : ""}`}
        >
          {cell}
        </td>
      ))}
    </tr>
  );
}

function B({ children }: { children: React.ReactNode }) {
  return <strong className="font-semibold text-[var(--text-primary)]">{children}</strong>;
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded bg-[var(--surface-2)] border border-[var(--border)] px-1.5 py-0.5 text-[0.85em]">
      {children}
    </code>
  );
}
