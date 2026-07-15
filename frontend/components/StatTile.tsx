/* Stat tile contract: label (sentence case, no trailing colon) · value · optional
   note. Values use proportional figures — tabular is for columns that align. */
export function StatTile({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <p className="text-sm text-[var(--text-secondary)]">{label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">{value}</p>
      {note && <p className="mt-1 text-xs text-[var(--text-muted)]">{note}</p>}
    </div>
  );
}

/* Hero figure — the one number the view leads with. Exactly one per page. */
export function HeroFigure({
  label,
  value,
  note,
}: {
  label: string;
  value: string;
  note?: string;
}) {
  return (
    <div>
      <p className="text-sm text-[var(--text-secondary)]">{label}</p>
      <p className="mt-1 text-6xl font-semibold tracking-tight leading-none">{value}</p>
      {note && <p className="mt-3 text-sm text-[var(--text-muted)]">{note}</p>}
    </div>
  );
}

/* Meter: the fill carries severity; the unfilled track is a lighter step of the
   same ramp, so state reads across the whole bar. */
export function Meter({
  label,
  used,
  total,
}: {
  label: string;
  used: number;
  total: number;
}) {
  const pct = total > 0 ? Math.min(100, (used / total) * 100) : 0;
  const fill =
    pct >= 100 ? "var(--critical)" : pct >= 80 ? "var(--warning)" : "var(--accent)";

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
      <div className="flex items-baseline justify-between gap-3">
        <p className="text-sm text-[var(--text-secondary)]">{label}</p>
        <p className="text-sm tabular text-[var(--text-muted)]">
          {used} / {total}
        </p>
      </div>
      <div
        className="mt-3 h-2 rounded-full overflow-hidden"
        style={{ background: "var(--accent-track)" }}
        role="meter"
        aria-valuenow={used}
        aria-valuemin={0}
        aria-valuemax={total}
        aria-label={label}
      >
        <div
          className="h-full rounded-full transition-[width]"
          style={{ width: `${pct}%`, background: fill }}
        />
      </div>
      <p className="mt-2 text-xs text-[var(--text-muted)]">
        {Math.max(0, total - used)} left today
      </p>
    </div>
  );
}

/* Status never rides on color alone — icon + label always travel together. */
export function StatusPill({ ok }: { ok: boolean }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-sm whitespace-nowrap">
      <span
        aria-hidden="true"
        className="grid place-items-center w-4 h-4 rounded-full text-white text-[10px] font-bold"
        style={{ background: ok ? "var(--good)" : "var(--critical)" }}
      >
        {ok ? "✓" : "✕"}
      </span>
      <span style={{ color: ok ? "var(--good-text)" : "var(--critical)" }}>
        {ok ? "Sent" : "Failed"}
      </span>
    </span>
  );
}
