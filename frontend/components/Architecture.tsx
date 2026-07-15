"use client";

import { motion, useReducedMotion } from "framer-motion";

const nodes = [
  { label: "You", sub: "“apply to these 10”" },
  { label: "Claude", sub: "researches, writes" },
  { label: "Setu", sub: "verifies, limits, sends" },
  { label: "Your Gmail", sub: "your account" },
  { label: "HR", sub: "receives it from you" },
];

/** The request path, drawn once. Horizontal on desktop, vertical on mobile —
 *  the same five nodes either way. */
export default function Architecture() {
  const reduce = useReducedMotion();

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 sm:p-10 shadow-[var(--shadow-sm)]">
      <ol className="flex flex-col md:flex-row md:items-stretch gap-3 md:gap-0">
        {nodes.map((node, i) => (
          <li key={node.label} className="flex md:flex-col md:flex-1 items-center gap-3 md:gap-0">
            <motion.div
              initial={reduce ? false : { opacity: 0, scale: 0.96 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ duration: 0.35, delay: i * 0.09 }}
              className="w-full md:text-center"
            >
              <div className="rounded-xl border border-[var(--border)] bg-[var(--plane)] px-4 py-3">
                <p className="font-semibold text-sm">{node.label}</p>
                <p className="mt-0.5 text-xs text-[var(--text-muted)]">{node.sub}</p>
              </div>
            </motion.div>

            {i < nodes.length - 1 && (
              <>
                <Connector vertical />
                <Connector />
              </>
            )}
          </li>
        ))}
      </ol>

      <div className="mt-8 space-y-3 text-sm text-[var(--text-secondary)] leading-relaxed max-w-2xl">
        <p>
          <strong>100% Secure for your inbox.</strong> Setu is designed with strict security limits—it will <em>never</em> read your inbox. It only has permission to send emails on your behalf.
        </p>
        <p>
          Nothing here holds your password, and nothing stores a token. Claude asks
          Setu to send; Setu asks Google, using a permission you granted and can
          revoke at any time. The mail leaves <em>your</em> account — so replies come back to
          your inbox, not ours.
        </p>
      </div>
    </div>
  );
}

function Connector({ vertical = false }: { vertical?: boolean }) {
  const base = vertical ? "md:hidden h-6 w-px my-1" : "hidden md:block h-px flex-1 mx-2 self-center";

  return (
    <svg
      className={`${base} shrink-0 text-[var(--accent)]`}
      viewBox={vertical ? "0 0 1 24" : "0 0 100 1"}
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <line
        x1={0}
        y1={0}
        x2={vertical ? 0 : 100}
        y2={vertical ? 24 : 0}
        stroke="currentColor"
        strokeWidth="2"
        className="flow-line"
        opacity={0.5}
      />
    </svg>
  );
}
