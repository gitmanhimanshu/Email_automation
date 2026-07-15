"use client";

import { motion, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";
import { Check, Wrench } from "lucide-react";

type Turn =
  | { kind: "user"; text: string }
  | { kind: "tool"; name: string; result: string }
  | { kind: "assistant"; text: string }
  | { kind: "sent"; text: string };

const script: Turn[] = [
  {
    kind: "user",
    text: "Acme is hiring a backend engineer. Apply for me.",
  },
  {
    kind: "tool",
    name: "get_my_profile",
    result: "resume_link saved · 68 of 80 left today",
  },
  {
    kind: "tool",
    name: "verify_hr_emails",
    result: "careers@acme.com — MX ok, found on acme.com/careers",
  },
  {
    kind: "assistant",
    text: "Here's the draft. It leads with the Postgres work from your last role, since their posting calls out query performance:\n\n“Hi — I'm applying for the Backend Engineer role…”\n\nSend it?",
  },
  { kind: "user", text: "yes, send" },
  {
    kind: "tool",
    name: "send_application",
    result: "sent · message_id 18f2a9c4d5e6b7a8",
  },
  {
    kind: "sent",
    text: "Sent from your Gmail. It's in your Sent folder, and their reply lands in your inbox.",
  },
];

export default function ChatDemo() {
  const [shown, setShown] = useState(0);
  const ref = useRef<HTMLDivElement>(null);
  const [started, setStarted] = useState(false);
  const reduce = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([entry]) => entry.isIntersecting && setStarted(true),
      { threshold: 0.25 }
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!started) return;
    if (reduce) {
      setShown(script.length);
      return;
    }
    if (shown >= script.length) return;
    const t = setTimeout(() => setShown((n) => n + 1), shown === 0 ? 300 : 900);
    return () => clearTimeout(t);
  }, [started, shown, reduce]);

  return (
    <div
      ref={ref}
      className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-4 sm:p-6 shadow-[var(--shadow-md)] min-h-[420px]"
    >
      <div className="space-y-3">
        {script.slice(0, shown).map((turn, i) => (
          <motion.div
            key={i}
            initial={reduce ? false : { opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <Bubble turn={turn} />
          </motion.div>
        ))}
      </div>
    </div>
  );
}

function Bubble({ turn }: { turn: Turn }) {
  if (turn.kind === "user") {
    return (
      <div className="flex justify-end">
        <p className="max-w-[85%] rounded-2xl rounded-br-sm bg-[var(--accent)] text-white px-4 py-2.5 text-sm">
          {turn.text}
        </p>
      </div>
    );
  }

  if (turn.kind === "tool") {
    return (
      <div className="flex items-start gap-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3.5 py-2.5">
        <Wrench size={13} className="mt-0.5 shrink-0 text-[var(--text-muted)]" />
        <div className="min-w-0">
          <code className="text-xs font-medium">{turn.name}</code>
          <p className="text-xs text-[var(--text-muted)] mt-0.5 break-words">{turn.result}</p>
        </div>
      </div>
    );
  }

  if (turn.kind === "sent") {
    return (
      <div className="flex items-start gap-2.5 rounded-xl border border-[var(--border)] bg-[var(--surface-2)] px-3.5 py-2.5">
        <span
          aria-hidden="true"
          className="mt-0.5 shrink-0 grid place-items-center w-4 h-4 rounded-full text-white"
          style={{ background: "var(--good)" }}
        >
          <Check size={10} strokeWidth={3} />
        </span>
        <p className="text-xs" style={{ color: "var(--good-text)" }}>
          {turn.text}
        </p>
      </div>
    );
  }

  return (
    <p className="max-w-[92%] text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
      {turn.text}
    </p>
  );
}
