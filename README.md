# Setu — Bridge AI to Opportunity

**Live:** [setu.mimanasa.online](https://setu.mimanasa.online) · **Connector URL:** `https://api.mimanasa.online/mcp`

Setu is an open-source **Model Context Protocol (MCP)** server that lets AI assistants (Claude, ChatGPT, Cursor, Windsurf, VS Code, and any other MCP client) send email from **your own Gmail** — researched by the assistant, written for the actual recipient, approved by you before anything leaves.

*Setu (सेतु) means "bridge" in Hindi.*

## Overview

An AI assistant can write a great email, but it doesn't have hands to send it. Setu is that pair of hands — and it deliberately owns the parts a model should *not* be trusted with: who the user is, how much they have already sent, whether an address is real, and the send itself.

Setu serves three roles, and the role changes what a good email looks like:

1. **Job seekers** — find openings and send applications, resume link attached (and verified as publicly openable first).
2. **Recruiters** — candidate outreach, with the job description along for the ride.
3. **Professionals** — meeting requests, follow-ups, client pitches, everyday outreach; links optional.

## Key features

- **Sends from your actual Gmail.** Emails appear in your Sent folder; replies land in your inbox. No third-party sending domain, no deliverability penalty.
- **Send-only by construction.** Setu requests exactly one Gmail scope: `gmail.send`. It *cannot* read your inbox — that is a missing permission, not a promise. No password is ever seen (Google OAuth) and **no token is ever stored** — the OAuth layer issues a fresh one per request.
- **Server-side guardrails, not prompt suggestions:**
  - Daily limit (default 80/user) and batch cap (25) to protect your Gmail reputation
  - Paced sending (default 5s between emails) so a run doesn't look like a bot
  - Duplicate prevention — every send is recorded; the same address is never emailed twice
  - Resume/portfolio link verification — Setu fetches your link and rejects it if it redirects to a sign-in page, so HR never sees "Request access"
  - Optional MX + citation checks (`VERIFY_HR_EMAILS=true`) that block addresses the model guessed from a naming pattern
- **General email too, not just applications.** `include_link=false` sends without your saved link — greetings, meeting requests, follow-ups.
- **SQLite or Postgres.** Zero-setup SQLite for local dev; set `DATABASE_URL` and the same code runs on Postgres (Neon/Supabase/Railway) for production.

## MCP tools

| Tool | What it does |
|---|---|
| `get_my_profile` | The signed-in user's role, saved link, plan, and remaining quota. Call first. |
| `set_role` | `job_seeker` \| `recruiter` \| `professional`. Asked, never inferred. |
| `save_link` | Saves the URL appended to emails. Fetched and validated before saving. |
| `verify_hr_emails` | MX-record + citation check for addresses the model found. Advisory by default. |
| `send_application` | Sends one email. Irreversible; shown to the user first. `include_link=false` skips the link. |
| `send_applications` | Batch send (max 25), paced. Same rules per email. |
| `get_sent_history` | Everything already sent — what makes duplicate prevention possible. |
| `get_my_stats` | The user's numbers at a glance — totals, companies reached, failures, quota, plan — for "show my stats". |

## Architecture

Built with **Python 3.12**, [FastMCP](https://gofastmcp.com), and the Gmail API. Three independent entry points share `core/`:

### 1. Hosted MCP server (`remote/`) — the real product
Streamable **HTTP** transport + Google OAuth (dynamic client registration). Any user connects from claude.ai/ChatGPT with one URL and a Google sign-in; nothing to install.

```bash
python -m remote.server          # http://localhost:8000/mcp
```

It also serves a small HTTP API for the web frontend:

| Route | Purpose |
|---|---|
| `GET /health` | Liveness + database reachability (used by Render health checks) |
| `GET /api/stats` | Per-user stats for the dashboard (Bearer = Google access token) |
| `POST /api/link` | Save/change the user's resume or portfolio link from the dashboard (same Bearer auth, same public-openability validation as the `save_link` tool) |
| `POST /api/visit` | Anonymous page-visit beacon for the analytics panel |
| `GET/POST /admin/api/*` | Admin panel: totals, users, visitors, plan changes (HTTP Basic via `ADMIN_EMAIL`/`ADMIN_PASSWORD`) |

### 2. Local MCP server (`mcp_server/`)
**stdio** transport for Claude Desktop / Cursor / local clients. You bring your own Google Cloud credentials; only you can use it.

```json
{
  "mcpServers": {
    "setu": { "command": "python", "args": ["-m", "mcp_server.server"] }
  }
}
```

### 3. Standalone desktop app (`app.py` / `main.py`)
No MCP client in the loop, so **Gemini** writes the emails. Flask web UI (`python app.py` → http://localhost:5000) or CLI (`python main.py`). Reads recipients from a public Google Sheet or manual entry.

## Self-hosting

### Prerequisites
- Python 3.10+
- A Google Cloud project with the **Gmail API** enabled
- An OAuth client — **Web application** for the hosted server, **Desktop app** for the local modes
- Only these scopes: `openid`, `userinfo.email`, `gmail.send` — never add `gmail.readonly`/`compose`/`modify`; they move the app into Google's restricted tier ($15k–75k annual CASA audit)

### Install

```bash
git clone https://github.com/gitmanhimanshu/Email_automation.git
cd Email_automation
python -m venv venv
venv\Scripts\activate            # Windows
source venv/bin/activate         # Mac/Linux
pip install -r remote/requirements.txt   # hosted server only
# or: pip install -r requirements.txt    # everything incl. desktop modes
```

### Configure

```bash
cp .env.example .env             # then fill it in
```

```env
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx
PUBLIC_BASE_URL=http://localhost:8000    # your domain in production
# DATABASE_URL=postgresql://...          # unset = SQLite (data/app.db)
ADMIN_EMAIL=you@gmail.com                # admin panel login (optional)
ADMIN_PASSWORD=change-me
```

Add the redirect URI in Google Console, exactly: `<PUBLIC_BASE_URL>/auth/callback`.

### Run & connect

```bash
python -m remote.server
```

- **claude.ai:** Settings → Connectors → Add custom connector → `https://your-domain.com/mcp`
- **Claude Code:** `claude mcp add --transport http setu https://your-domain.com/mcp`
- **VS Code / Cursor / Windsurf:** add the same URL as a remote MCP server

End-to-end test against your own inbox (real OAuth, real send):

```bash
python -m remote.server        # terminal 1
python -m remote.test_local    # terminal 2
```

### Deploy

The repo ships a Dockerfile and a Render blueprint ([render.yaml](render.yaml)) with the health check preconfigured — connect the repo on [Render](https://render.com) as a Blueprint, set the env vars, done. Railway works the same way ([railway.json](railway.json)). Use Postgres in production (Neon free tier is plenty); on ephemeral filesystems SQLite is wiped on every deploy.

Full deploy guide, including Google verification and the OAuth publishing-status trap: **[remote/README.md](remote/README.md)**.

## Frontend

The landing page, docs, dashboard, and admin panel live in a separate repo: [setu-frontend](https://github.com/gitmanhimanshu/setu-frontend) (Next.js 15, deployed on Vercel).

## Contributing

Contributions are welcome — see **[CONTRIBUTING.md](CONTRIBUTING.md)** for setup, style, and what makes a good PR. Found a security issue? Please follow **[SECURITY.md](SECURITY.md)** instead of opening a public issue.

## License

[MIT](LICENSE) © 2026 Himanshu Yadav
