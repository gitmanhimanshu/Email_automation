# MCP Setup — Claude ke saath use karna

Is mode mein **Claude khud emails likhta hai** aur ye server sirf bhejta hai.

Kyun? Kyunki Claude ke paas tumhari conversation ka context hota hai — tumhari actual
skills, kis company mein kya bolna hai, kaunsa project relevant hai. Ek fixed Gemini
prompt ke paas ye kabhi nahi hoga. Isliye **MCP mode mein Gemini ki zaroorat nahi hai**,
aur `GEMINI_API_KEY` optional ho jaati hai.

Gemini sirf standalone mode (`app.py` / `main.py`) mein chalta hai, jahan koi model
loop mein nahi hota.

---

## 1. Google OAuth credentials banao

Har user apni khud ki client ID/secret use karta hai — koi shared credential nahi hai.

1. [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials) kholo
2. **Gmail API** enable karo
3. **Create Credentials → OAuth client ID** → type: **Desktop app**
4. Client ID aur secret copy karo

> **Scope sirf `gmail.send` hai.** Ye app tumhara inbox padh hi nahi sakta —
> token chori bhi ho jaye to koi tumhari mails nahi dekh sakta.

## 2. `.env` bharo

`.env.example` ko `.env` naam se copy karke:

```env
YOUR_NAME=Himanshu Yadav
YOUR_EMAIL=you@gmail.com
RESUME_LINK=https://your-resume-link.com
EMAIL_DELAY=5

GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx

# MCP mode mein iski zaroorat nahi
# GEMINI_API_KEY=
```

## 3. Ek baar Gmail login karo

```bash
pip install -r requirements.txt
python authorize.py
```

Browser khulega → jis Gmail se bhejna hai usse login karo → Allow.

Token `~/.email_automation/token.json` mein save hota hai — project folder mein nahi,
taaki galti se repo mein commit na ho jaye.

> Ye step MCP server khud nahi kar sakta. Wo Claude ke neeche headless chalta hai,
> jahan browser prompt bas hang kar jaata.

## 4. Claude Desktop se connect karo

`claude_desktop_config.json` kholo:

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "email-automation": {
      "command": "python",
      "args": ["C:\\path\\to\\Email_automation\\mcp_server\\server.py"]
    }
  }
}
```

Windows mein backslash double karna zaroori hai (`\\`). Path absolute hona chahiye —
server kisi bhi folder se launch ho jaayega.

Claude Desktop restart karo. Ab tumhe tools icon mein `email-automation` dikhega.

**Claude Code ke liye:**

```bash
claude mcp add email-automation -- python "C:\path\to\Email_automation\mcp_server\server.py"
```

---

## Tools

| Tool | Kya karta hai |
|---|---|
| `get_sender_profile` | Tumhara naam, email, resume link + Gmail ready hai ya nahi |
| `load_recipients_from_sheet` | Public Google Sheet se HR contacts |
| `check_already_contacted` | Kis HR ko pehle mail ja chuka hai |
| `send_email` | Ek email bhejo |
| `send_bulk_emails` | Batch bhejo, beech mein delay ke saath |
| `get_sent_log` | Ab tak kya kya bheja |

## Claude se kaise baat karein

```
Mujhe Bangalore ki 10 fintech startups ke HR ko job application bhejni hai,
Backend Engineer role ke liye. Pehle mera profile check karo, phir har company
ke liye alag email likho aur mujhe dikhao — approve karne ke baad hi bhejna.
```

Claude HR emails khud dhoondhega, har company ke liye alag content likhega,
tumhe dikhayega, aur approve karne par `send_bulk_emails` call karega.

Sheet se:

```
Ye sheet load karo: <URL>
Jinko pehle mail nahi gaya sirf unko bhejo.
```

---

## Safety

Emails **irreversible** hain — bhej diye to wapas nahi aayenge. Isliye:

- Har tool description Claude ko batati hai ki bhejne se pehle approval le
- `send_bulk_emails` ek call mein **max 25** emails — taaki tum beech mein review kar sako
- `check_already_contacted` se same HR ko dobara mail nahi jaata
- Har send `~/.email_automation/sent_emails.json` mein log hota hai

Pehli baar `send_email` se khud ko ek test mail bhej ke dekh lo.

---

## Troubleshooting

**"Gmail is not authorized"** → `python authorize.py` chalao

**"Google did not recognize the OAuth client"** → `.env` mein client ID/secret galat hai,
ya Google Cloud se client delete ho gaya. Theek karke `python authorize.py` dobara chalao.

**Claude ko tools nahi dikh rahe** → config JSON mein path check karo (backslash `\\`),
Claude Desktop pura restart karo. `python "C:\path\to\mcp_server\server.py"` khud terminal
mein chala ke dekho — koi import error to nahi aa raha.

**"The sheet is not public"** → Sheet → Share → "Anyone with the link" → Viewer
