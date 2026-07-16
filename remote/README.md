# Hosted MCP Server — Deploy Guide

Ye wo version hai jisme **koi bhi user** claude.ai / ChatGPT se connect karke apni
Gmail se job applications bhej sakta hai. User ko kuch install nahi karna — bas
"Sign in with Google".

Local wala version (`mcp_server/`) sirf tumhare laptop pe chalta hai. Ye alag cheez hai.

---

## Flow

```
1. User claude.ai mein tumhara connector URL add karta hai
2. Claude → tumhara /register  (dynamic client registration)
3. User → Google consent → "Send email on your behalf" → Allow
4. Google → tumhara /auth/callback → token
5. User: "Bangalore ki hiring fintech companies dhundo, HR ko apply karo"
6. Claude web search karke HR emails dhundhta hai
7. Claude har company ke liye alag email likhta hai, user ko dikhata hai
8. User approve karta hai
9. Claude → send_applications → tumhara server → user ki Gmail → HR
```

Resume link user ek baar `save_resume_link` se deta hai, phir har email mein
server khud append karta hai. Resume link bina send **block** hota hai.


---

## ⚠️ Sabse important rule

**Kabhi bhi `gmail.readonly`, `gmail.compose`, ya `gmail.modify` scope mat add karna.**

| Scope | Tier | Cost |
|---|---|---|
| `gmail.send` (jo hum use karte hain) | **Sensitive** | Free verification, ~2-6 hafte |
| `gmail.readonly` / `compose` / `modify` | **Restricted** | **CASA security assessment — $15k-75k, har saal repeat** |

Ek line add karne se tumhara free product ek paid annual audit ban jaayega.
`config.SCOPES` mein comment isi liye likha hai.

---

## 1. Google Cloud setup

> Console ka UI 2025 mein badla tha. "OAuth consent screen" ab **Google Auth Platform**
> hai aur settings teen jagah bant gayi hain. Purane tutorials wo purana menu
> dhundhwate hain jo ab exist nahi karta.

| Step | Kahan | Kya karna |
|---|---|---|
| 1 | [Project banao](https://console.cloud.google.com/projectcreate) | Naam do, phir upar wahi project selected rakhna |
| 2 | [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com) | **Enable** |
| 3 | [Branding](https://console.cloud.google.com/auth/branding) | App name, support email, developer contact |
| 4 | [Audience](https://console.cloud.google.com/auth/audience) | User type **External** → **Publish app** |
| 5 | [Data Access](https://console.cloud.google.com/auth/scopes) | Scopes add karo (neeche) |
| 6 | [Clients](https://console.cloud.google.com/auth/clients) | **Create client** → credentials milengi |

**Step 5 — sirf ye teen scopes:**

```
openid
https://www.googleapis.com/auth/userinfo.email
https://www.googleapis.com/auth/gmail.send
```

`gmail.readonly` galti se tick mat kar dena — wo restricted tier hai (upar wali table dekho).

**Step 6 — client settings:**

- Application type: **Web application**
  ← *Desktop app nahi! Wo local `mcp_server/` ke liye hai, ye nahi.*
- Authorized redirect URI:
  - Localhost: `http://localhost:8000/auth/callback`
  - Production: `https://your-domain.com/auth/callback`

Client ID aur secret popup mein dikhengi. **Secret sirf ek baar dikhti hai** — copy kar lo.

> `redirect_uri_mismatch` sabse common error hai. URI **bilkul exactly** match karna
> chahiye = `PUBLIC_BASE_URL` + `/auth/callback`. Trailing slash, `http` vs `https`,
> ya `127.0.0.1` vs `localhost` — koi bhi farak fail karega.

> Scope badalne ke baad purana token invalid ho jaata hai. `~/.fastmcp/` ka cached
> token clear karke dobara login karna padega.

Privacy Policy aur Terms of Service URLs verification ke liye chahiye honge
(section 5), par localhost testing ke liye nahi.

### ⚠️ Publishing status — sabse important setting

OAuth consent screen pe **Publishing status** hi decide karta hai ki kaun tumhara
app use kar sakta hai. Ye sabse zyada confuse karne wali cheez hai:

| | **Testing** | **In production** (unverified) | **In production** (verified) |
|---|---|---|---|
| Kaun login kar sakta | Sirf Test users list wale | **Koi bhi** | Koi bhi |
| Test users list | **Manually add karni padegi** | **Chahiye hi nahi** | Chahiye hi nahi |
| Warning screen | Nahi | "Google hasn't verified this app" | Nahi |
| Total cap | 100 test users | **100 users (total, kabhi bhi)** | Unlimited |
| Refresh token | **7 din mein expire!** | Expire nahi hota | Expire nahi hota |

**Asli users ke liye "Publish app" dabao.** Testing mode mein do problem hain: har
user ko manually add karna padega (jo scale nahi karta), aur har user ko **har hafte
dobara login** karna padega — tumhe lagega code toot gaya, par ye Google ka rule hai.

Production-unverified mein user ko warning screen dikhega (Advanced → "Go to app"),
par koi bhi login kar sakta hai. 100 users ke baad verification hi rasta hai.

([publishing status](https://developers.google.com/identity/protocols/oauth2) ·
[app audience](https://support.google.com/cloud/answer/15549945?hl=en) ·
[unverified apps](https://support.google.com/cloud/answer/7454865?hl=en))

---

## 2. Environment variables

```env
GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxx
PUBLIC_BASE_URL=https://your-domain.com
DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/setu?sslmode=require
DAILY_SEND_LIMIT=80
EMAIL_DELAY=5
VERIFY_HR_EMAILS=false
ENV=production

# Admin panel (frontend /admin page). Dono set nahi kiye to admin API
# routes 503 dete hain — panel exist hi nahi karta. Password strong rakho;
# isse har user ka data dikhta hai aur plans badalte hain.
ADMIN_EMAIL=you@gmail.com
ADMIN_PASSWORD=change-me
```

`PUBLIC_BASE_URL` **HTTPS hona chahiye**. HTTP pe FastMCP non-secure cookies ka
warning dega aur claude.ai connect nahi karega.

### Database

| | Kab | Setup |
|---|---|---|
| **Postgres** | Production | `DATABASE_URL` set karo |
| **SQLite** | Local dev | Kuch nahi — default hai |

`DATABASE_URL` set hai to Postgres, warna SQLite. Code dono ke liye same hai.

**Production mein Postgres use karo** ([Neon](https://neon.tech) free tier 0.5GB
kaafi hai). Fayde:

- **Koi volume mount nahi chahiye** — Railway/Render pe ek setup step kam, aur
  volume bhoolne se data udne ka risk hi khatam
- Redeploy pe kuch nahi khota
- Backups mil jaate hain, banane nahi padte

Neon setup: [neon.tech](https://neon.tech) → project banao → connection string copy
karo → `DATABASE_URL` mein daalo. Bas.

> **Firestore kyun nahi:** data relational hai (users → sends, COUNT queries,
> `IN` lookups). Firestore count queries **reads bill** karti hain — matlab har
> send se pehle daily-limit check paisa kharch karega. Aur uski `in` query **30
> values pe cap** hai, jabki hamara batch 25 hai. Postgres yahan natural fit hai.

## 3. Deploy — Railway (recommended)

1. Code GitHub pe push karo
2. [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Dockerfile khud detect ho jaayega (`railway.json` isi liye hai)
4. **Variables** tab → ye daalo:
   ```
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxx
   DATABASE_URL=postgresql://...neon.tech/setu?sslmode=require
   ENV=production
   ```
   > `PUBLIC_BASE_URL` aur `PORT` **mat daalo** — Railway khud inject karta hai
   > aur code use uthata hai (`RAILWAY_PUBLIC_DOMAIN`).
5. **Settings → Networking → Generate Domain** → `setu-production.up.railway.app` milega
6. Google Console mein redirect URI add karo:
   `https://setu-production.up.railway.app/auth/callback`
7. Redeploy

> Neon (`DATABASE_URL`) use kar rahe ho to **volume ki zaroorat nahi**. Agar SQLite
> pe hi rehna hai to Settings → Volumes → mount path `/app/data` **zaroori** hai,
> warna har deploy pe users ka saara data wipe ho jaayega.

Connector URL: `https://setu-production.up.railway.app/mcp`

**Local docker test:**
```bash
docker build -t setu .
docker run -p 8000:8000 --env-file .env -v "$(pwd)/data:/app/data" setu
```

**Render pe deploy karna hai?** Repo root ka [render.yaml](../render.yaml) blueprint
use karo: Render → New + → Blueprint → repo select → env vars bharo (upar wale hi;
`PUBLIC_BASE_URL`/`PORT` yahan bhi mat daalna — Render `RENDER_EXTERNAL_HOSTNAME`
inject karta hai). Health check `/health` pe pehle se configured hai. Free plan pe
**persistent disk nahi milti**, isliye `DATABASE_URL` (Neon) zaroori hai — warna har
deploy pe data wipe. Fly.io bhi chalega — Dockerfile + volume support hai.

**Health check:** har deploy pe `GET /health` available hai — 200 + database
status deta hai, koi auth nahi chahiye. Render/Railway ka health check aur
uptime monitors isi pe lagao.

### ❌ Vercel pe deploy mat karna

Vercel serverless hai; ye server usse ladta hai. Teen cheezein tootengi:

| Problem | Kyun |
|---|---|
| **SQLite mar jaayegi** | Vercel ka filesystem ephemeral hai — sirf `/tmp` likhne layak, aur wo bhi invocations ke beech nahi bachta. Users ka data randomly gayab hoga. |
| **Bulk send timeout** | `send_applications` = 25 emails × 5s delay = **125s**. Hobby limit 60s. Batch beech mein katega — kuch mails gaye, kuch nahi, user ko pata nahi. |
| **OAuth proxy ki yaaddasht** | DCR client registrations aur token state persist karne padte hain. Serverless pe har invocation alag instance — users randomly logout honge. |

Le jaana **possible** hai, par tab: SQLite → Postgres, FastMCP storage → Redis,
aur sleep loop hatao. Asli rewrite hai, aur phir bhi platform se ladte rahoge.

Frontend website Vercel pe rakho — wo uska sahi use hai. Ye server Railway pe.

([Vercel limits](https://vercel.com/docs/functions/limitations) ·
[max duration](https://vercel.com/docs/functions/configuring-functions/duration))

---

## 3b. Localhost pe test karo (deploy se pehle)

Domain aur deploy ki zaroorat nahi. Google `http://localhost` redirect URI allow
karta hai — HTTPS rule ka ye ek exception hai.

**Setup:**

1. Cloud Console mein OAuth client (Web application) ke redirect URI mein ye add karo:
   ```
   http://localhost:8000/auth/callback
   ```
2. Apne aap ko login karne do — do mein se ek:
   - **Publish app** dabao (recommended) → koi bhi login kar sakta hai, tum bhi
   - Ya **Test users → apna Gmail add karo** (agar abhi publish nahi karna)

   Dono mein se kuch nahi kiya to *"Access blocked: app has not completed
   verification"* milega.
3. `.env`:
   ```env
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxx
   PUBLIC_BASE_URL=http://localhost:8000
   DATABASE_PATH=data/app.db
   ```

**Chalao — do terminal:**

```bash
pip install -r remote/requirements.txt

# Terminal 1
python -m remote.server

# Terminal 2
python -m remote.test_local
```

`test_local.py` browser kholega (asli Google consent), phir pura chain check karega:
resume gate, email guard, aur ek asli test email tumhe hi bhejega.

**Claude Code se localhost pe connect:**

```bash
claude mcp add --transport http setu http://localhost:8000/mcp
```

**claude.ai localhost tak nahi pahunch sakta** — wo cloud pe hai, tumhara laptop nahi
dekh sakta. Uske liye tunnel chahiye:

```bash
cloudflared tunnel --url http://localhost:8000
# ya: ngrok http 8000
```

Jo HTTPS URL mile usse `PUBLIC_BASE_URL` mein daalo, **aur Cloud Console ke redirect
URI mein bhi add karo** (`https://xxx.trycloudflare.com/auth/callback`), phir server
restart karo. Tunnel URL har baar badalta hai, to redirect URI bhi har baar update
karna padega.

## 4. Connect from Claude

**claude.ai:** Settings → Connectors → Add custom connector → `https://your-domain.com/mcp`

**Claude Code:**
```bash
claude mcp add --transport http setu https://your-domain.com/mcp
```

**ChatGPT:** Settings → Connectors → Add (developer mode on hona chahiye)

Pehli baar connect karne pe Google consent khulega.

---

## 5. Google verification — asli timeline

Verification tak tumhara app **100 users** pe capped hai, aur har user ko ek
scary "Google hasn't verified this app" screen dikhega.

Chahiye:
- Privacy Policy + Terms of Service (live URLs, working)
- Domain verification via [Search Console](https://search.google.com/search-console)
- Demo video (YouTube): pura OAuth flow dikhana — user consent se lekar email send tak
- Scope justification: kyun `gmail.send` chahiye

Time: **~2-6 hafte**, back-and-forth ke saath. Aaj hi apply kar do — code ready
hone ka intezaar mat karo, kyunki review parallel mein chalta rahega.

Tab tak: Test users list mein 100 log add kar sakte ho (OAuth consent screen →
Test users). Wo bina warning ke use kar payenge.

---

## Guardrails (jo server enforce karta hai, model nahi)

Ye model ke bharose nahi chhode gaye — server khud check karta hai:

- **`verify_hr_emails`** — advisory tool. MX record check + `source_url` dekhta hai,
  aur guessed addresses (`"guessed from pattern"`, `"inferred"`, khali) flag karta hai.
  Claude chahe to call kare. **Send ko block nahi karta** (default).
- **`VERIFY_HR_EMAILS=true`** — ise `.env` mein set karo to upar wala check **mandatory**
  ho jaata hai: har send se pehle verify hoga aur guessed address reject hoga.
  Default **off** hai. On karne layak tab hai jab bounce rate deliverability kharab
  karne lage — guessed addresses bounce hoti hain, aur bounces user ka Gmail sending
  reputation girati hain.
- **Resume gate** — resume link save nahi hai to `send_application` /
  `send_applications` **refuse** karte hain, aur error Claude ko bolta hai ki user se
  link maango. Ye sirf hint nahi hai — server rokta hai, kyunki bina resume ki
  application bekaar hai aur wo HR contact hamesha ke liye zaya ho jaata hai.
- **Resume link publicly openable hai ya nahi** — `save_resume_link` link ko actually
  fetch karta hai. Agar wo sign-in page pe redirect hui (matlab Drive file share nahi
  ki) to reject, kyunki HR ko "Request access" dikhta aur user ko pata bhi nahi chalta.
  Network fail ho to allow kar deta hai — inconclusive check kisi ko job apply karne
  se nahi rokna chahiye.
- **Daily limit** — default 80/user/24h (Gmail ki apni limit ~500 hai)
- **Batch limit** — ek call mein max 25, taaki user beech mein review kar sake
- **Dedupe** — same HR ko dobara mail nahi

**Jo ye nahi kar sakta:** mailbox exist karta hai ya nahi, ye MX check nahi bata
sakta — sirf domain mail le sakta hai ya nahi. Mailbox-level verification ke liye
ZeroBounce/NeverBounce jaisi paid API chahiye. Isliye published `careers@` /
`jobs@` addresses ko personal guesses se prefer karo.

---

## Security notes

- Server **koi Google token store nahi karta**. OAuth proxy har request pe fresh
  access token deta hai. DB mein sirf email, naam, resume link, send history hai.
- Har user apne hi data tak limited hai — sab kuch Google `sub` se keyed hai.
- Scope send-only hai, isliye ek leaked token se bhi koi inbox nahi padh sakta.

---

## Sources

- [Gmail API scopes (send = sensitive)](https://developers.google.com/workspace/gmail/api/auth/scopes)
- [Sensitive scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/sensitive-scope-verification)
- [Restricted scope verification (CASA)](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification)
- [Unverified apps & the 100-user cap](https://support.google.com/cloud/answer/7454865?hl=en)
- [FastMCP Google OAuth](https://gofastmcp.com/integrations/google)
