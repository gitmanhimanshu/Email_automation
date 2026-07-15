import type { Metadata } from "next";
import Link from "next/link";
import DocsLayout from "@/components/DocsLayout";
import { CodeBlock } from "@/components/CodeWindow";
import { MCP_URL, SETU_URL } from "@/lib/site";

export const metadata: Metadata = {
  title: "HTTP API",
  description:
    "Setu's HTTP surface: the MCP endpoint, OAuth discovery, and the one REST endpoint the dashboard reads.",
};

const codes = [
  ["200", "OK"],
  ["401", "Missing, invalid, or expired bearer token"],
  ["404", "No such route"],
];

export default function ApiPage() {
  return (
    <DocsLayout>
      <article className="max-w-2xl">
        <h1 className="text-4xl font-semibold tracking-tight">HTTP API</h1>
        <p className="mt-4 text-lg text-[var(--text-secondary)] leading-relaxed">
          Almost everything Setu does is reached over MCP, not REST — the tools
          are the API. This page covers the raw HTTP surface underneath.
        </p>

        <p className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm text-[var(--text-secondary)] leading-relaxed">
          If you&apos;re integrating an assistant, you want{" "}
          <Link href="/docs/tools" className="text-[var(--accent)] hover:underline">
            Tools
          </Link>
          , not this page. There is exactly one REST endpoint, and it exists to
          feed the dashboard.
        </p>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">Base URL</h2>
          <div className="mt-3">
            <CodeBlock lang="text" code={SETU_URL} />
          </div>
        </section>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">Endpoints</h2>
          <div className="mt-4 scroll-x rounded-xl border border-[var(--border)]">
            <table className="w-full text-sm border-collapse">
              <thead>
                <tr className="bg-[var(--surface-2)]">
                  <Th>Method</Th>
                  <Th>Endpoint</Th>
                  <Th>Description</Th>
                </tr>
              </thead>
              <tbody>
                <Row
                  method="POST"
                  path="/mcp"
                  desc="The MCP endpoint. Streamable HTTP. Requires a bearer token; returns 401 with a WWW-Authenticate header pointing at the resource metadata."
                />
                <Row
                  method="GET"
                  path="/api/stats"
                  desc="Your profile and send history, for the dashboard. Bearer token = a Google access token."
                />
                <Row
                  method="GET"
                  path="/.well-known/oauth-protected-resource/mcp"
                  desc="RFC 9728 resource metadata. How a client discovers the authorization server."
                />
                <Row
                  method="GET"
                  path="/.well-known/oauth-authorization-server"
                  desc="OAuth 2.1 server metadata: authorize, token, and registration endpoints."
                />
                <Row
                  method="POST"
                  path="/register"
                  desc="Dynamic client registration. Google doesn't support DCR, so Setu proxies it — this is what makes remote MCP clients able to connect at all."
                />
                <Row method="GET" path="/authorize" desc="Starts the OAuth flow. Redirects to Google." />
                <Row method="POST" path="/token" desc="Exchanges an authorization code for an access token." />
                <Row method="GET" path="/auth/callback" desc="Where Google redirects back. Must match the URI registered in Google Cloud Console exactly." />
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">
            GET /api/stats
          </h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            Read-only. The token names the user, so a caller can only ever read
            their own rows — there is no user ID parameter to tamper with.
          </p>

          <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Request
          </h3>
          <div className="mt-2">
            <CodeBlock
              lang="bash"
              code={`curl ${SETU_URL}/api/stats \\
  -H "Authorization: Bearer <google_access_token>"`}
            />
          </div>

          <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Response
          </h3>
          <div className="mt-2">
            <CodeBlock
              lang="json"
              code={`{
  "email": "you@gmail.com",
  "name": "Himanshu Yadav",
  "resume_link": "https://drive.google.com/file/d/…",
  "total_sent": 42,
  "total_failed": 1,
  "sent_last_24h": 12,
  "daily_limit": 80,
  "companies": 38,
  "recent": [
    {
      "to_email": "careers@acme.com",
      "company": "Acme",
      "subject": "Application for Backend Engineer at Acme",
      "success": true,
      "error": null,
      "sent_at": "2026-07-15T09:22:04+00:00"
    }
  ]
}`}
            />
          </div>

          <h3 className="mt-6 text-xs font-semibold uppercase tracking-wide text-[var(--text-muted)]">
            Status codes
          </h3>
          <div className="mt-2 scroll-x rounded-xl border border-[var(--border)]">
            <table className="w-full text-sm border-collapse">
              <tbody>
                {codes.map(([code, meaning]) => (
                  <tr key={code} className="border-b border-[var(--border)] last:border-0">
                    <td className="px-4 py-2.5 font-mono text-xs tabular w-20">{code}</td>
                    <td className="px-4 py-2.5 text-[var(--text-secondary)] text-sm">
                      {meaning}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">
            Connecting a client
          </h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            You shouldn&apos;t need to implement any of this by hand — an MCP
            client does the discovery, registration, and PKCE for you. Point it
            at:
          </p>
          <div className="mt-3">
            <CodeBlock lang="text" code={MCP_URL} />
          </div>
          <p className="mt-4 text-sm text-[var(--text-secondary)] leading-relaxed">
            The flow: the client fetches the resource metadata, registers itself
            at <Code>/register</Code>, sends the user to <Code>/authorize</Code>,
            and Setu hands off to Google. Google doesn&apos;t support dynamic
            client registration, which is why Setu sits in the middle as an OAuth
            proxy rather than pointing clients straight at Google.
          </p>
        </section>

        <section className="mt-12">
          <h2 className="text-2xl font-semibold tracking-tight">Rate limits</h2>
          <p className="mt-3 text-[var(--text-secondary)] leading-relaxed">
            Sending limits are per user and enforced in the server, not in the
            HTTP layer: 80 emails per rolling 24 hours, 25 per batch call. Over
            the limit, the tool returns <Code>success: false</Code> with a reason
            — not an HTTP error.
          </p>
        </section>
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

function Row({ method, path, desc }: { method: string; path: string; desc: string }) {
  return (
    <tr className="border-b border-[var(--border)] last:border-0">
      <td className="px-4 py-3 align-top">
        <span
          className="text-[10px] font-semibold px-1.5 py-0.5 rounded"
          style={{
            background: "var(--accent-soft)",
            color: method === "POST" ? "var(--accent)" : "var(--text-secondary)",
          }}
        >
          {method}
        </span>
      </td>
      <td className="px-4 py-3 align-top">
        <code className="text-xs whitespace-nowrap">{path}</code>
      </td>
      <td className="px-4 py-3 align-top text-xs text-[var(--text-secondary)] leading-relaxed">
        {desc}
      </td>
    </tr>
  );
}

function Code({ children }: { children: React.ReactNode }) {
  return (
    <code className="rounded bg-[var(--surface-2)] border border-[var(--border)] px-1.5 py-0.5 text-[0.85em]">
      {children}
    </code>
  );
}
