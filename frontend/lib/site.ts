/** One place for the facts the site repeats, so they can't drift apart. */

export const SETU_URL =
  process.env.NEXT_PUBLIC_SETU_URL ?? "http://localhost:8000";

export const MCP_URL = `${SETU_URL}/mcp`;

export const SITE_URL =
  process.env.NEXT_PUBLIC_SITE_URL ?? "https://setu.mimamsa.dev";

export const GITHUB_URL =
  process.env.NEXT_PUBLIC_GITHUB_URL ?? "https://github.com/gitmanhimanshu/setu";

export const CONTACT_EMAIL = "himanshuyada70@gmail.com";

export const AUTHOR = {
  name: "Himanshu Yadav",
  role: "Built and maintained by",
  github: "https://github.com/gitmanhimanshu",
  linkedin: "https://www.linkedin.com/in/himanshu-yadav-5ba28921b/",
};

export const MIMANASA = {
  name: "Mimanasa",
  site: "https://www.mimanasa.online/",
  edu: "https://edu.mimanasa.online/",
};

export const TAGLINE = {
  hi: "एक मार्गदर्शक, आपके सपनों और अवसरों के बीच।",
  en: "A guide, between your dreams and your opportunities.",
};

export const LIMITS = {
  perDay: 80,
  perBatch: 25,
  defaultDelaySeconds: 5,
};

/**
 * MCP clients.
 *
 * `tested` is the honest distinction: Setu is a remote MCP server speaking
 * Streamable HTTP + OAuth, so any spec-compliant client should work — but
 * "should work" and "we ran it" are different claims, and the site says which
 * is which rather than implying endorsement by any of these vendors.
 */
export const CLIENTS = [
  { name: "Claude", note: "claude.ai connectors", tested: true },
  { name: "Claude Code", note: "CLI", tested: true },
  { name: "ChatGPT", note: "Developer mode, paid plans", tested: true },
  { name: "Cursor", note: "remote MCP", tested: false },
  { name: "VS Code", note: "MCP extension", tested: false },
  { name: "Windsurf", note: "remote MCP", tested: false },
  { name: "Cline", note: "remote MCP", tested: false },
  { name: "Continue.dev", note: "remote MCP", tested: false },
];

export type Tool = {
  name: string;
  purpose: string;
  input: { name: string; type: string; required: boolean; desc: string }[];
  output: string;
  example: string;
  destructive?: boolean;
};

export const TOOLS: Tool[] = [
  {
    name: "get_my_profile",
    purpose:
      "Who you are, whether a resume link is saved, and how much of today's quota is left. The assistant should call this first — everything else depends on it.",
    input: [],
    output:
      "email, name, resume_link, resume_link_saved, sent_last_24h, daily_limit, remaining_today, max_per_batch, setup_needed",
    example: `{
  "email": "you@gmail.com",
  "name": "Himanshu Yadav",
  "resume_link": "https://drive.google.com/file/d/…",
  "resume_link_saved": true,
  "sent_last_24h": 12,
  "daily_limit": 80,
  "remaining_today": 68,
  "max_per_batch": 25,
  "setup_needed": null
}`,
  },
  {
    name: "save_resume_link",
    purpose:
      "Saves your resume URL. Setu fetches the link to check an HR reader could actually open it — a Drive file you forgot to share is rejected here rather than silently failing in someone's inbox.",
    input: [
      {
        name: "resume_link",
        type: "string",
        required: true,
        desc: "Public http(s) URL — Drive, Dropbox, personal site",
      },
    ],
    output: "success, resume_link, detail — or an error explaining why it was rejected",
    example: `{
  "success": false,
  "error": "This link is not shared publicly — it redirects to a
   sign-in page, so HR would see 'Request access' instead of the
   resume. Open it in Drive, click Share, and set 'Anyone with
   the link' to Viewer.",
  "resume_link": "https://drive.google.com/file/d/…"
}`,
  },
  {
    name: "verify_hr_emails",
    purpose:
      "Advisory. Checks whether an address's domain can actually receive mail, and flags addresses that look constructed from a naming pattern rather than found on a page. Does not block sending unless VERIFY_HR_EMAILS is enabled on the server.",
    input: [
      {
        name: "candidates",
        type: "Candidate[]",
        required: true,
        desc: "Each: email, company, source_url (the page you saw it on)",
      },
    ],
    output: "checked, usable, rejected, results[] with reasons and warnings",
    example: `{
  "checked": 2,
  "usable": 1,
  "rejected": 1,
  "results": [
    { "email": "careers@acme.com", "ok": true,
      "detail": "MX: aspmx.l.google.com" },
    { "email": "hr@acme-inc.io", "ok": false,
      "reasons": ["acme-inc.io: domain does not exist"] }
  ]
}`,
  },
  {
    name: "send_application",
    purpose:
      "Sends one application from your Gmail. Irreversible. Refuses if no resume link is saved or the daily limit is spent. Your resume link is appended automatically.",
    input: [
      { name: "to", type: "string", required: true, desc: "Recipient address" },
      { name: "subject", type: "string", required: true, desc: "Subject line" },
      { name: "body", type: "string", required: true, desc: "Plain text body" },
      { name: "company", type: "string", required: false, desc: "For your history" },
      { name: "source_url", type: "string", required: false, desc: "Where the address came from" },
    ],
    output: "success, to, subject, message_id — or success:false with error",
    example: `{
  "success": true,
  "to": "careers@acme.com",
  "subject": "Application for Backend Engineer at Acme",
  "message_id": "18f2a9c4d5e6b7a8"
}`,
    destructive: true,
  },
  {
    name: "send_applications",
    purpose:
      "Sends a batch, pausing between each so Gmail doesn't read the run as automated. Capped at 25 per call, so you review as you go instead of finding out afterwards.",
    input: [
      {
        name: "applications",
        type: "Application[]",
        required: true,
        desc: "Each: to, subject, body, company, source_url — max 25",
      },
      {
        name: "delay_seconds",
        type: "int",
        required: false,
        desc: "Pause between sends. Defaults to the server's EMAIL_DELAY (5s)",
      },
    ],
    output: "sent, failed, skipped, skipped_details[], results[], remaining_today",
    example: `{
  "success": true,
  "sent": 8,
  "failed": 0,
  "skipped": 1,
  "skipped_details": [
    { "to": "hr@x.com", "reason": "daily limit reached" }
  ],
  "remaining_today": 60
}`,
    destructive: true,
  },
  {
    name: "get_sent_history",
    purpose:
      "Everything you've sent through Setu, newest first. The record survives across sessions, which is what makes duplicate-send prevention possible.",
    input: [
      { name: "limit", type: "int", required: false, desc: "How many rows. Default 20" },
    ],
    output: "sent_last_24h, daily_limit, entries[]",
    example: `{
  "sent_last_24h": 12,
  "daily_limit": 80,
  "entries": [
    { "to_email": "careers@acme.com", "company": "Acme",
      "success": true, "message_id": "18f2a9c4d5e6b7a8",
      "sent_at": "2026-07-15T09:22:04+00:00" }
  ]
}`,
  },
];

export const FAQS: { q: string; a: string }[] = [
  {
    q: "What is MCP?",
    a: "Model Context Protocol — an open standard for connecting AI assistants to external tools. Instead of every assistant building its own Gmail integration, a tool exposes an MCP server once and any compatible client can use it. Setu is such a server.",
  },
  {
    q: "Do I need to install anything?",
    a: "No. Setu is a hosted remote MCP server, not a package. You add one URL to your assistant and sign in with Google. There is no npm install, no config file to hand-edit, and nothing running on your machine.",
  },
  {
    q: "Which assistants work with Setu?",
    a: "Claude (claude.ai connectors), Claude Code, and ChatGPT (Developer mode, paid plans) are tested. Setu speaks standard Streamable HTTP MCP with OAuth, so other spec-compliant clients — Cursor, VS Code, Windsurf, Cline, Continue.dev — should work, but we haven't verified each one.",
  },
  {
    q: "How is Gmail authenticated?",
    a: "Google OAuth. You sign in on Google's own page; Setu never sees your password. Google returns a token scoped to sending only, and that token is what Setu uses on your behalf.",
  },
  {
    q: "Can Setu read my inbox?",
    a: "No — and not as a policy choice. Setu requests exactly one Gmail permission: gmail.send. Reading mail requires gmail.readonly, which Setu never asks for and cannot use. Even a stolen token could not open your mail.",
  },
  {
    q: "Where do HR replies go?",
    a: "Straight to your inbox, like any other email. Setu never sees them — the send-only scope means there is no mechanism by which it could.",
  },
  {
    q: "Does Setu store my Google password or tokens?",
    a: "Neither. There is no password (Google handles login), and no token is stored — the OAuth layer supplies a fresh one per request. The database holds your email, name, resume link, and send history. Nothing else.",
  },
  {
    q: "Is my resume uploaded to your server?",
    a: "No. Setu stores a link, not a file, and appends that link to each application. Your resume stays wherever you host it — Drive, Dropbox, your own site.",
  },
  {
    q: "Why does Setu reject my resume link?",
    a: "Almost always because it isn't shared publicly. Setu fetches the URL; if it redirects to a sign-in page, HR would see 'Request access' instead of your resume — and you'd never know. Set the file to 'Anyone with the link can view'.",
  },
  {
    q: "Can it send without me seeing the email first?",
    a: "The tools tell the assistant to show you every recipient and a full draft, and to get approval before calling a send tool. That instruction is strong but it is guidance to a model, not a mechanical lock. The mechanical limits are elsewhere: 25 per batch, 80 per day, no duplicates, and no send at all without a resume link.",
  },
  {
    q: "How many emails can I send?",
    a: `${LIMITS.perDay} per day, ${LIMITS.perBatch} per batch. Gmail's own ceiling is higher, but staying well under it protects your account's sending reputation — and a batch cap means you review as you go.`,
  },
  {
    q: "Why the delay between emails?",
    a: "Sending a burst is one of the patterns Gmail treats as automation. A few seconds between each keeps the run looking like a person working through a list, which is what it is.",
  },
  {
    q: "Will it email the same company twice?",
    a: "No. Setu records every successful send and can check a list against that history before you send. The record persists across sessions and clients.",
  },
  {
    q: "Why does Google say 'this app isn't verified'?",
    a: "Because it hasn't finished Google's review yet. Click Advanced → Go to Setu. The word 'unsafe' is Google's wording for 'not reviewed', not a finding about Setu. The permission screen after it is the real answer: Send email on your behalf, and nothing else.",
  },
  {
    q: "Can I revoke access?",
    a: "Any time, without asking us. Go to myaccount.google.com/permissions, find Setu, and remove it. The token stops working immediately.",
  },
  {
    q: "Does Setu write the emails?",
    a: "No — your assistant does. That's the point of the design. Claude knows your background from the conversation and can read the actual job posting; a template on our server never could. Setu owns the parts a model shouldn't be trusted with: identity, limits, and the send itself.",
  },

  {
    q: "What happens to my data if I stop using it?",
    a: "Revoke access in your Google account and the token dies. Email support to have your row deleted outright — the data is a resume link and a send log, so there is not much to it.",
  },
];
