/** Shape of GET /api/stats on the Setu server. */
export type Send = {
  to_email: string;
  company: string | null;
  subject: string | null;
  success: boolean;
  error: string | null;
  sent_at: string;
};

export type Stats = {
  email: string;
  name: string | null;
  resume_link: string | null;
  total_sent: number;
  total_failed: number;
  sent_last_24h: number;
  daily_limit: number;
  companies: number;
  recent: Send[];
};

export const SETU_URL =
  process.env.NEXT_PUBLIC_SETU_URL ?? "http://localhost:8000";

/**
 * Fetch the signed-in user's stats.
 *
 * The token is a Google access token — the same one the MCP flow issues. The
 * server resolves it to an identity itself; the browser never sees anyone
 * else's data because the token is the only thing that names a user.
 */
export async function fetchStats(accessToken: string): Promise<Stats> {
  const res = await fetch(`${SETU_URL}/api/stats`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });

  if (res.status === 401) throw new Error("Your session expired. Sign in again.");
  if (!res.ok) throw new Error(`Setu server returned ${res.status}`);

  return res.json();
}

export function formatWhen(iso: string): string {
  const then = new Date(iso).getTime();
  const mins = Math.round((Date.now() - then) / 60000);

  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 1440) return `${Math.round(mins / 60)}h ago`;
  if (mins < 10080) return `${Math.round(mins / 1440)}d ago`;
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}
