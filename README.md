# Setu - Bridge AI to Opportunity

Setu is an open-source **Model Context Protocol (MCP)** server that allows AI assistants (Claude, ChatGPT, Cursor, Windsurf, etc.) to securely automate email outreach directly from your Gmail account.

**Frontend Repository:** [Setu Frontend](https://github.com/gitmanhimanshu/setu-frontend)

## Overview

An AI assistant can write a great email, but it doesn't have hands to send it. Setu bridges this gap by exposing Gmail capabilities to AI models via the standard Model Context Protocol (MCP). 

Setu is built for:
1. **Job Seekers:** Automatically find jobs and send applications with your resume attached.
2. **Recruiters:** Do candidate outreach at scale with Job Descriptions.
3. **Professionals:** Send cold emails, follow-ups, or client pitches with your portfolio.

## Key Features

- **Sends from your actual Gmail:** Emails show up in your "Sent" folder, and replies come straight to your inbox.
- **100% Secure & Privacy First:** Requests ONLY the `gmail.send` scope. It cannot read a single email in your inbox. No passwords are ever stored (uses Google OAuth).
- **Paced Sending:** Adds a 5-second gap between emails by default so Gmail doesn't flag the run as automation.
- **Rate Limited:** Strict server-side limits (e.g. 80/day, 25/batch) to protect your Gmail reputation.
- **Duplicate Prevention:** Every sent email is recorded in a SQLite database to prevent emailing the same person twice.
- **Link Verification:** Checks if your Resume/Portfolio Google Drive link is public before sending, preventing access request bounces.

---

## MCP Tools Provided

Setu provides the following tools to the LLM:

1. `get_my_profile`: Fetches the user's role, saved link, plan, and quota.
2. `set_role`: Sets the role (`job_seeker`, `recruiter`, `professional`).
3. `save_link`: Saves the URL appended to every email (Resume/JD/Portfolio).
4. `verify_hr_emails`: Checks MX records to verify if an email address can receive mail.
5. `send_application`: Sends a single email.
6. `send_applications`: Sends a batch of emails (max 25 per call).
7. `get_sent_history`: Retrieves the user's send history to avoid duplicates.

---

## Architecture & Modes

Setu is built with **Python**, **Flask**, and the **mcp** Python SDK. It supports two modes:

### 1. Remote SaaS Mode (SSE / Web)
This is the default mode used for the hosted platform. It uses Server-Sent Events (SSE) over HTTP to communicate with MCP clients (like ChatGPT/Claude web interfaces) and uses OAuth for Google authentication.
- **Entry point:** `app.py`
- **Database:** `data/setu.db` (User profiles, tokens, limits, history)

### 2. Standalone Local Mode (stdio)
If you want to run Setu locally for yourself (e.g. in Cursor or Claude Code CLI) without the web dashboard, you can use the stdio transport mode.
- **Entry point:** `main.py`
- **Authentication:** Local `credentials.json` flow.

---

## Self-Hosting / Local Setup

### 1. Prerequisites
- Python 3.10+
- A Google Cloud Project with the **Gmail API** enabled.
- OAuth 2.0 Client Credentials (Desktop App for Standalone, Web Application for SaaS).

### 2. Installation
```bash
git clone https://github.com/gitmanhimanshu/Email_automation.git
cd Email_automation
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your details:
```env
# For Remote SaaS Mode
SECRET_KEY=your_secure_random_key
OAUTH_CLIENT_ID=your_google_oauth_client_id.apps.googleusercontent.com
OAUTH_CLIENT_SECRET=your_google_oauth_client_secret
SITE_URL=http://localhost:3000
```

### 4. Running the Server

**To run the SaaS Web Server (SSE transport + OAuth):**
```bash
python app.py
```
*Server runs on `http://localhost:8000`*

**To run the Local Standalone Server (stdio transport):**
Put your Google Cloud Desktop `credentials.json` in the root folder, then run:
```bash
python main.py
```

---

## Using with MCP Clients

Once deployed (or running via ngrok), add Setu to your AI assistant:

**Claude (claude.ai):**
Go to Settings -> Connectors -> Add Custom Connector -> Use the URL `https://your-domain.com/mcp`

**Claude Code CLI:**
```bash
claude mcp add --transport http setu https://your-domain.com/mcp
```

**Cursor IDE:**
Add this to your `mcp.json`:
```json
{
  "mcpServers": {
    "setu": {
      "command": "python",
      "args": ["main.py"]
    }
  }
}
```

---

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

## License
MIT License
