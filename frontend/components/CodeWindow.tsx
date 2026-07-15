"use client";

import { useEffect, useState } from "react";
import { Check, Copy } from "lucide-react";

export function CopyButton({ value, label = "Copy" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button
      onClick={copy}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-2)] transition-colors"
      aria-label={copied ? "Copied" : label}
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? "Copied" : label}
    </button>
  );
}

export function CodeBlock({
  code,
  filename,
  lang,
}: {
  code: string;
  filename?: string;
  lang?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] overflow-hidden shadow-[var(--shadow-sm)]">
      <div className="flex items-center justify-between gap-3 px-3 py-2 border-b border-[var(--border)] bg-[var(--surface-2)]">
        <span className="text-xs font-medium text-[var(--text-muted)] truncate">
          {filename ?? lang ?? "code"}
        </span>
        <CopyButton value={code} />
      </div>
      <pre className="scroll-x p-4 text-[13px] leading-relaxed">
        <code className="font-mono">{code}</code>
      </pre>
    </div>
  );
}

/* Terminal that types itself out once, on view. Decorative — the same content
   is in the docs as selectable text, so nothing depends on the animation. */
export function AnimatedTerminal({ lines }: { lines: { text: string; dim?: boolean }[] }) {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (shown >= lines.length) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setShown(lines.length);
      return;
    }
    const t = setTimeout(() => setShown((n) => n + 1), shown === 0 ? 350 : 420);
    return () => clearTimeout(t);
  }, [shown, lines.length]);

  return (
    <div
      className="rounded-xl overflow-hidden border border-[var(--border)] shadow-[var(--shadow-lg)]"
      style={{ background: "var(--terminal-bg)" }}
    >
      <div className="flex items-center gap-1.5 px-4 py-3 border-b border-white/[0.07]">
        <Dot color="#ff5f57" />
        <Dot color="#febc2e" />
        <Dot color="#28c840" />
        <span className="ml-2 text-[11px] text-white/40 font-mono">setu — connect</span>
      </div>
      <div
        className="p-4 font-mono text-[12.5px] leading-[1.75] min-h-[188px]"
        style={{ color: "var(--terminal-ink)" }}
      >
        {lines.slice(0, shown).map((line, i) => (
          <div key={i} className="fade-up whitespace-pre-wrap break-all">
            <span className={line.dim ? "text-white/40" : ""}>{line.text}</span>
            {i === shown - 1 && shown < lines.length && (
              <span className="caret ml-0.5">▋</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function Dot({ color }: { color: string }) {
  return <span className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />;
}
