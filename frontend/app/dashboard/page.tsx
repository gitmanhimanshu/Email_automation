"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import Logo from "@/components/Logo";
const fade = (delay: number) => ({
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.6, delay, ease: [0.22, 1, 0.36, 1] as const },
});

const chips = [
  "Send history",
  "Delivery analytics",
  "Job pipeline",
  "Quota tracker",
  "Resume insights",
];

export default function Dashboard() {
  return (
    <main className="min-h-[80vh] flex items-center justify-center px-6 py-20 overflow-hidden">
      <div className="w-full max-w-2xl text-center">

        {/* Logo + Brand */}
        <motion.div {...fade(0)} className="flex flex-col items-center gap-3 mb-10">
          <div
            className="rounded-2xl p-4 grid place-items-center"
            style={{
              background: "var(--accent-glow)",
              boxShadow: "0 0 60px 12px var(--accent-glow)",
            }}
          >
            <Logo size={48} />
          </div>
          <div>
            <p
              lang="hi"
              className="text-3xl sm:text-4xl text-[var(--text-primary)]"
              style={{ fontWeight: 600, letterSpacing: "-0.01em" }}
            >
              सेतु
            </p>
            <p
              className="mt-1 text-[11px] text-[var(--text-muted)] uppercase font-sans"
              style={{ fontWeight: 500, letterSpacing: "0.35em" }}
            >
              Setu
            </p>
          </div>
        </motion.div>

        {/* Main heading — animated word by word */}
        <motion.h1
          {...fade(0.15)}
          className="text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight leading-tight"
        >
          {"Dashboard is".split(" ").map((word, i) => (
            <motion.span
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.25 + i * 0.12 }}
              className="inline-block mr-[0.3em]"
            >
              {word}
            </motion.span>
          ))}
          <br />
          <motion.span
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.55, ease: "easeOut" }}
            className="text-[var(--accent)] inline-block"
          >
            coming soon.
          </motion.span>
        </motion.h1>

        {/* Description */}
        <motion.p
          {...fade(0.55)}
          className="mt-5 text-[var(--text-secondary)] text-base sm:text-lg leading-relaxed max-w-lg mx-auto"
        >
          We&apos;re building a full analytics dashboard — send history,
          delivery rates, job matches, and quota tracking — all in one place.
        </motion.p>



        {/* Feature chips */}
        <motion.div {...fade(0.65)} className="mt-10 flex flex-wrap justify-center gap-2">
          {chips.map((chip, i) => (
            <motion.span
              key={chip}
              initial={{ opacity: 0, scale: 0.85 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.4, delay: 0.75 + i * 0.08 }}
              whileHover={{ scale: 1.05, y: -2 }}
              className="px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-xs text-[var(--text-secondary)] hover:border-[var(--border-strong)] hover:shadow-[var(--shadow-sm)] transition-all cursor-default"
            >
              {chip}
            </motion.span>
          ))}
        </motion.div>

        {/* CTA */}
        <motion.div
          {...fade(0.95)}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3"
        >
          <Link
            href="/docs"
            className="group inline-flex items-center gap-2 px-5 py-2.5 rounded-full bg-[var(--text-primary)] text-[var(--plane)] font-medium text-sm hover:opacity-90 transition-opacity"
          >
            Read the docs
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="group-hover:translate-x-0.5 transition-transform"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </Link>
          <Link
            href="/"
            className="px-5 py-2.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-sm font-medium hover:border-[var(--border-strong)] transition-colors"
          >
            Back to home
          </Link>
        </motion.div>

        {/* Bottom note */}
        <motion.p
          {...fade(1.05)}
          className="mt-12 text-xs text-[var(--text-muted)]"
        >
          Meanwhile, your send history is accessible via the{" "}
          <Link
            href="/docs/tools"
            className="underline underline-offset-2 hover:text-[var(--text-secondary)] transition-colors"
          >
            get_sent_history
          </Link>{" "}
          tool.
        </motion.p>
      </div>
    </main>
  );
}
