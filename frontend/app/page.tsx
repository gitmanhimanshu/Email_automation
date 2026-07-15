import Link from "next/link";
import {
  ArrowRight,
  CheckCircle2,
  Clock,
  FileText,
  Gauge,
  KeyRound,
  Layers,
  MailCheck,
  ShieldOff,
  Sparkles,
  Terminal,
  UserCheck,
} from "lucide-react";
import Architecture from "@/components/Architecture";
import Aurora from "@/components/Aurora";
import ChatDemo from "@/components/ChatDemo";
import { AnimatedTerminal } from "@/components/CodeWindow";
import Faq from "@/components/Faq";
import Reveal from "@/components/Reveal";
import { CLIENTS, GITHUB_URL, LIMITS, MCP_URL, TAGLINE } from "@/lib/site";

const features = [
  {
    icon: MailCheck,
    title: "Sends from your Gmail",
    body: "Not a noreply@ nobody answers. It leaves your account, shows in your Sent folder, and replies come back to your inbox.",
  },
  {
    icon: ShieldOff,
    title: "Cannot read your inbox",
    body: "Setu asks Google for one permission: gmail.send. Reading mail needs a scope it never requests and cannot use.",
  },
  {
    icon: FileText,
    title: "Resume link, checked",
    body: "Paste it once and it rides along on every application. Setu fetches it first — a Drive file you forgot to share gets rejected here, not silently in someone's inbox.",
  },
  {
    icon: UserCheck,
    title: "Address verification",
    body: "Optional MX and citation checks catch addresses a model invented from a naming pattern. Those bounce, and bounces cost you deliverability.",
  },
  {
    icon: Layers,
    title: "Batches with a ceiling",
    body: `${LIMITS.perBatch} per call, ${LIMITS.perDay} per day. Small enough that you review as you go instead of finding out afterwards.`,
  },
  {
    icon: Clock,
    title: "Paced sending",
    body: `A ${LIMITS.defaultDelaySeconds}s gap between sends by default. A burst is one of the patterns Gmail reads as automation.`,
  },
  {
    icon: CheckCircle2,
    title: "No duplicate sends",
    body: "Every send is recorded. Setu can check a fresh list against that history before a single email goes out.",
  },
  {
    icon: KeyRound,
    title: "OAuth, no passwords",
    body: "You sign in on Google's page. Setu never sees a password, and stores no token — the OAuth layer issues a fresh one per request.",
  },
  {
    icon: Terminal,
    title: "Open source",
    body: "Server, desktop version, and this site are all in the repo. Self-host with your own Google credentials if you'd rather.",
  },
];

const steps = [
  { n: 1, title: "Add the URL", body: "One connector URL into Claude, ChatGPT, or any MCP client. Nothing to install." },
  { n: 2, title: "Sign in with Google", body: "Grant one permission — send email. That's the whole auth step." },
  { n: 3, title: "Save your resume link", body: "Setu checks it's publicly openable, then appends it to every application." },
  { n: 4, title: "Ask in plain language", body: "\u201CFind fintech startups hiring backend engineers and apply.\u201D Your assistant does the research." },
  { n: 5, title: "Read the drafts", body: "Every recipient and a full draft, before anything leaves. You approve." },
  { n: 6, title: "Sent as you", body: "Setu delivers through Gmail, paced and logged. Replies go straight to you." },
];

const terminalLines = [
  { text: "$ claude mcp add --transport http setu \\" },
  { text: `    ${MCP_URL}`, dim: true },
  { text: "" },
  { text: "\u2713 Connector registered", dim: true },
  { text: "\u2713 Opening Google sign-in\u2026", dim: true },
  { text: "\u2713 Granted: Send email on your behalf", dim: true },
  { text: "" },
  { text: "6 tools available. Ask Claude to apply somewhere." },
];

export default function Home() {
  return (
    <main>
      {/* Hero */}
      <section className="relative isolate">
        <Aurora />
        <div className="mx-auto max-w-6xl px-6 pt-20 pb-16 sm:pt-28 grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          <div>
            <span className="inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)]">
              <Sparkles size={12} className="text-[var(--accent)]" />
              Model Context Protocol server
            </span>

            <h1 className="mt-6 text-4xl sm:text-6xl font-semibold tracking-tight leading-[1.03]">
              Connect AI to Gmail
              <br />
              in minutes.
            </h1>

            <p
              lang="hi"
              className="mt-5 text-lg text-[var(--accent)] leading-relaxed"
            >
              {TAGLINE.hi}
            </p>

            <p className="mt-4 text-lg text-[var(--text-secondary)] leading-relaxed max-w-xl">
              Setu is an MCP server that lets Claude, ChatGPT, or Cursor send job
              applications from your own Gmail — researched by the assistant,
              written for the actual posting, approved by you before it leaves.
            </p>

            <div className="mt-9 flex flex-wrap gap-3">
              <Link
                href="/docs"
                className="group inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[var(--text-primary)] text-[var(--plane)] font-medium hover:opacity-90 transition-opacity"
              >
                Get started
                <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
              </Link>
              <a
                href={GITHUB_URL}
                target="_blank"
                rel="noreferrer noopener"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-full border border-[var(--border)] bg-[var(--surface)] font-medium hover:border-[var(--border-strong)] transition-colors"
              >
                GitHub
              </a>
            </div>

            <p className="mt-6 text-sm text-[var(--text-muted)]">
              Start with <span className="font-medium text-[var(--text-primary)]">5 free emails</span>. No install — it&apos;s a URL.
            </p>
          </div>

          <Reveal delay={0.1}>
            <AnimatedTerminal lines={terminalLines} />
          </Reveal>
        </div>
      </section>

      {/* How it works — right after the hero: showing the thing working beats
          explaining the protocol behind it. */}
      <section id="how" className="mx-auto max-w-6xl px-6 py-20 border-t border-[var(--border)] scroll-mt-20">
        <Reveal>
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">
            How it works
          </h2>
          <p className="mt-4 text-[var(--text-secondary)] max-w-2xl leading-relaxed">
            Six steps, once. After that it&apos;s a sentence in a chat window.
          </p>
        </Reveal>

        <div className="mt-10 grid lg:grid-cols-2 gap-12">
          <ol className="relative">
            <span
              className="absolute left-[15px] top-2 bottom-2 w-px bg-[var(--border)]"
              aria-hidden="true"
            />
            {steps.map((step, i) => (
              <Reveal key={step.n} delay={i * 0.05}>
                <li className="relative flex gap-4 pb-7 last:pb-0">
                  <span className="relative z-[1] shrink-0 grid place-items-center w-8 h-8 rounded-full border border-[var(--border)] bg-[var(--surface)] text-xs font-semibold tabular">
                    {step.n}
                  </span>
                  <div className="pt-1">
                    <h3 className="font-semibold text-sm">{step.title}</h3>
                    <p className="mt-1 text-sm text-[var(--text-secondary)] leading-relaxed">
                      {step.body}
                    </p>
                  </div>
                </li>
              </Reveal>
            ))}
          </ol>

          <Reveal delay={0.1}>
            <ChatDemo />
          </Reveal>
        </div>
      </section>

      {/* Works with */}
      <section className="mx-auto max-w-6xl px-6 py-14 border-t border-[var(--border)]">
        <p className="text-sm text-[var(--text-muted)]">
          Works with any MCP client
        </p>
        <div className="mt-6 flex flex-wrap gap-2">
          {CLIENTS.map((client) => (
            <span
              key={client.name}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl border border-[var(--border)] bg-[var(--surface)] text-sm"
            >
              <span className="font-medium">{client.name}</span>
              <span className="text-xs text-[var(--text-muted)]">{client.note}</span>
              {client.tested && (
                <span
                  className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full"
                  style={{ background: "var(--accent-soft)", color: "var(--accent)" }}
                >
                  tested
                </span>
              )}
            </span>
          ))}
        </div>
        <p className="mt-5 text-xs text-[var(--text-muted)] max-w-2xl leading-relaxed">
          Setu speaks standard Streamable HTTP MCP with OAuth, so any compliant
          client should connect. &ldquo;Tested&rdquo; marks the ones we&apos;ve actually run —
          the rest are expected to work but unverified. These are integrations,
          not endorsements: none of these vendors sponsor or affiliate with Setu.
        </p>
      </section>

      {/* What is MCP */}
      <section id="what-is-mcp" className="mx-auto max-w-6xl px-6 py-20 border-t border-[var(--border)] scroll-mt-20">
        <Reveal>
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">
            What is MCP?
          </h2>
          <div className="mt-5 max-w-2xl space-y-4 text-[var(--text-secondary)] leading-relaxed">
            <p>
              An AI assistant can write a good application email. What it
              can&apos;t do, on its own, is send one — it has no hands. Every
              tool it touches has to be wired in, and until recently every
              assistant needed its own wiring.
            </p>
            <p>
              <strong className="text-[var(--text-primary)] font-semibold">
                Model Context Protocol
              </strong>{" "}
              is the standard that fixed that. A tool exposes its capabilities
              once, over MCP, and any compatible client can use them — the same
              way a website works in any browser.
            </p>
            <p>
              Setu is one of those servers. It exposes six things an assistant
              can do with your Gmail, and the assistant decides when to use them.
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.1} className="mt-10">
          <Architecture />
        </Reveal>
      </section>

      {/* Features */}
      <section className="mx-auto max-w-6xl px-6 py-20 border-t border-[var(--border)]">
        <Reveal>
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">
            Why this one
          </h2>
          <p className="mt-4 text-[var(--text-secondary)] max-w-2xl leading-relaxed">
            Setu owns the parts a language model shouldn&apos;t be trusted with:
            who you are, what&apos;s already been sent, how much is too much, and
            the send itself.
          </p>
        </Reveal>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => (
            <Reveal key={feature.title} delay={Math.min(i * 0.04, 0.2)}>
              <div className="h-full rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-md)] transition-all">
                <span className="grid place-items-center w-9 h-9 rounded-lg bg-[var(--surface-2)] text-[var(--accent)]">
                  <feature.icon size={17} strokeWidth={2} />
                </span>
                <h3 className="mt-4 font-semibold">{feature.title}</h3>
                <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
                  {feature.body}
                </p>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* Security */}
      <section id="security" className="mx-auto max-w-6xl px-6 py-20 border-t border-[var(--border)] scroll-mt-20">
        <Reveal>
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">
            What Setu can and can&apos;t do
          </h2>
          <p className="mt-4 text-[var(--text-secondary)] max-w-2xl leading-relaxed">
            Most tools ask you to trust a privacy policy. The list below
            isn&apos;t policy — it&apos;s the permission Setu holds. The things
            in the right column aren&apos;t things Setu declines to do. They&apos;re
            things it has no mechanism for.
          </p>
        </Reveal>

        <div className="mt-10 grid md:grid-cols-2 gap-4">
          <Reveal>
            <div className="h-full rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <h3 className="flex items-center gap-2 font-semibold">
                <Dot ok /> Can
              </h3>
              <ul className="mt-4 space-y-3 text-sm text-[var(--text-secondary)]">
                <Item ok>Send an email as you, when you approve it</Item>
                <Item ok>Read your name and email address</Item>
                <Item ok>Store your resume link and send history</Item>
              </ul>
            </div>
          </Reveal>

          <Reveal delay={0.06}>
            <div className="h-full rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">
              <h3 className="flex items-center gap-2 font-semibold">
                <Dot /> Cannot
              </h3>
              <ul className="mt-4 space-y-3 text-sm text-[var(--text-secondary)]">
                <Item>Open your inbox or read a single message</Item>
                <Item>See replies from HR — those go only to you</Item>
                <Item>Know your password. Google handles login</Item>
                <Item>Keep access after you revoke it</Item>
              </ul>
            </div>
          </Reveal>
        </div>

        <Reveal delay={0.1}>
          <div className="mt-4 grid sm:grid-cols-3 gap-4">
            <Fact icon={KeyRound} title="No tokens at rest">
              The OAuth layer supplies a fresh access token per request. There is
              no credential in the database to steal.
            </Fact>
            <Fact icon={Gauge} title="Limits in code">
              {LIMITS.perDay}/day and {LIMITS.perBatch}/batch are enforced by the
              server, not suggested to the model.
            </Fact>
            <Fact icon={ShieldOff} title="Revoke anytime">
              myaccount.google.com/permissions → remove Setu. The token dies
              immediately, without asking us.
            </Fact>
          </div>
        </Reveal>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-6xl px-6 py-20 border-t border-[var(--border)] scroll-mt-20">
        <Reveal>
          <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">
            Questions
          </h2>
        </Reveal>
        <Reveal delay={0.05} className="mt-8">
          <Faq />
        </Reveal>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-6xl px-6 pb-8">
        <Reveal>
          <div className="relative overflow-hidden rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-8 sm:p-14 text-center">
            <div
              className="absolute inset-x-0 -top-24 h-48 pointer-events-none"
              style={{
                background:
                  "radial-gradient(50% 60% at 50% 100%, var(--accent-glow), transparent 70%)",
              }}
              aria-hidden="true"
            />
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight">
              One URL. Two minutes.
            </h2>
            <p className="mt-4 text-[var(--text-secondary)] max-w-lg mx-auto leading-relaxed">
              Add the connector, sign in with Google, paste your resume link.
              That&apos;s the entire setup.
            </p>
            <Link
              href="/docs"
              className="group mt-8 inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[var(--text-primary)] text-[var(--plane)] font-medium hover:opacity-90 transition-opacity"
            >
              Read the docs
              <ArrowRight size={15} className="group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </Reveal>
      </section>
    </main>
  );
}

function Dot({ ok = false }: { ok?: boolean }) {
  return (
    <span
      aria-hidden="true"
      className="grid place-items-center w-5 h-5 rounded-full text-white text-xs font-bold"
      style={{ background: ok ? "var(--good)" : "var(--critical)" }}
    >
      {ok ? "\u2713" : "\u2715"}
    </span>
  );
}

function Item({ children, ok = false }: { children: React.ReactNode; ok?: boolean }) {
  return (
    <li className="flex items-start gap-2.5">
      <span
        aria-hidden="true"
        className="mt-1.5 w-1 h-1 rounded-full shrink-0"
        style={{ background: ok ? "var(--good)" : "var(--critical)" }}
      />
      <span>
        <span className="sr-only">{ok ? "Can: " : "Cannot: "}</span>
        {children}
      </span>
    </li>
  );
}

function Fact({
  icon: Icon,
  title,
  children,
}: {
  icon: typeof KeyRound;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <span className="grid place-items-center w-8 h-8 rounded-lg bg-[var(--surface-2)] text-[var(--accent)]">
        <Icon size={15} />
      </span>
      <h3 className="mt-3 font-semibold text-sm">{title}</h3>
      <p className="mt-1.5 text-xs text-[var(--text-secondary)] leading-relaxed">
        {children}
      </p>
    </div>
  );
}

