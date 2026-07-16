# Security Policy

Setu sends email from users' own Gmail accounts, so security reports are taken
seriously and handled quickly.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Email **himanshuyada70@gmail.com** with:

- What you found and where (file, endpoint, or flow)
- Steps to reproduce
- What an attacker could do with it

You will get an acknowledgement within a few days. Once fixed, you are welcome
to be credited in the release notes — say so in your report.

## Scope notes for researchers

- The Gmail scope is send-only (`gmail.send`); the server stores **no Google
  tokens** — a fresh access token arrives per request via the OAuth proxy.
- The database holds: email, name, role, a user-supplied link, send history,
  and anonymous visit rows. That is the entire blast radius of a data leak;
  reports that demonstrate access to another user's rows are highest priority.
- `/admin/api/*` is HTTP Basic against `ADMIN_EMAIL`/`ADMIN_PASSWORD` env vars
  and is disabled (503) when they are unset. Brute-force resistance relies on
  the operator choosing a strong password — hardening PRs welcome.
- CORS on the JSON APIs is deliberately `*`: every route authenticates via an
  explicit `Authorization` header and never via cookies.

## Supported versions

Only the latest `main` is supported. There are no backported fixes.
