# Contributing to Setu

Thanks for considering a contribution! This file is the five-minute version of
everything you need.

## Dev setup

```bash
git clone https://github.com/gitmanhimanshu/Email_automation.git
cd Email_automation
python -m venv venv && source venv/bin/activate   # venv\Scripts\activate on Windows
pip install -r remote/requirements.txt
cp .env.example .env    # fill in your own Google OAuth client (Web application type)
python -m remote.server # http://localhost:8000 — /health should answer immediately
```

SQLite is the default database, so there is nothing else to install. To work
against Postgres, set `DATABASE_URL` in `.env` — the code is identical either way.

For a real end-to-end check (actual OAuth, actual Gmail send **to yourself**):

```bash
python -m remote.server        # terminal 1
python -m remote.test_local    # terminal 2
```

## Project layout

| Path | What lives there |
|---|---|
| `remote/` | The hosted MCP server — tools, storage, guardrails, admin API. Most changes land here. |
| `mcp_server/` | Local stdio MCP server (bring-your-own credentials) |
| `core/` | Shared Gmail/config code used by the desktop modes |
| `app.py`, `main.py` | Standalone desktop modes (Flask UI / CLI, Gemini-written content) |

## Ground rules

1. **Never widen the Gmail scope.** `gmail.send` only. Adding `gmail.readonly`,
   `compose`, or `modify` moves the app into Google's restricted tier (an
   annual paid CASA audit) and breaks the "cannot read your inbox" guarantee
   the whole product is built on. PRs that widen scope will be declined.
2. **Guardrails live on the server.** Anything that protects the user — limits,
   dedupe, link checks — must be enforced in Python, not requested politely in
   a tool description. Tool descriptions guide the model; the server decides.
3. **No tokens in storage.** The OAuth layer hands us a fresh access token per
   request. Keep it that way — the database should never hold anything worth
   stealing.
4. **Keep SQL portable.** Storage runs on both SQLite and Postgres from the
   same queries (`?` placeholders, rewritten automatically). Test any schema
   change against both; migrations go in `storage.MIGRATIONS`.
5. **Secrets stay out of git.** Real values live in `.env` (gitignored);
   `.env.example` carries placeholders only.

## Making a change

- Fork, branch from `main`, keep the diff focused on one thing.
- Match the surrounding code style — this codebase favours small functions,
  plain SQL, and comments that explain *why*, not *what*.
- Run `python -m py_compile` on files you touched and exercise the affected
  flow (for tool changes, `remote/test_local.py` drives the real chain).
- Describe in the PR what breaks without your change — a reproducible failure
  beats a description.

## Reporting bugs & ideas

Open a GitHub issue with what you did, what you expected, and what happened
instead. For anything security-sensitive, **do not open a public issue** — see
[SECURITY.md](SECURITY.md).
