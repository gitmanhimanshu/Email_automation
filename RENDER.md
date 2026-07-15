# Render pe Deploy — Step by Step

Ye guide hosted MCP server (`remote/`) ko [Render](https://render.com) pe deploy
karne ke liye hai. Railway wala tarika [remote/README.md](remote/README.md) mein
hai — dono mein se ek chuno, server same hai.

**Pehle Google Cloud setup complete karo** — OAuth client, scopes, publishing
status. Wo pura [remote/README.md § 1](remote/README.md) mein likha hai; yahan
repeat nahi kar rahe.

---

## Kya chahiye

- GitHub pe pushed repo (Render GitHub se hi deploy karta hai)
- Google OAuth client ID + secret (type: **Web application**)
- [Neon](https://neon.tech) ka free Postgres — **Render free plan pe zaroori hai**
  (neeche kyun likha hai)

## ⚠️ Free plan pe SQLite mat use karna

Render ke **free plan pe persistent disk nahi milti**. SQLite use kiya to har
deploy/restart pe users ka saara data ud jaayega — resume links, send history,
sab. Isliye:

| Plan | Database |
|---|---|
| Free | **Neon Postgres** (`DATABASE_URL` set karo) — ye bhi free hai |
| Starter+ | Neon Postgres (recommended) ya SQLite + persistent disk mounted at `/app/data` |

Neon setup 2 minute ka hai: [neon.tech](https://neon.tech) → project banao →
connection string copy karo. Bas.

---

## Option A: Blueprint se (recommended — 1 click)

Repo mein [render.yaml](render.yaml) already hai.

1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint**
2. Apna GitHub repo connect karo
3. Render `render.yaml` padh lega aur ye env vars poochega:
   ```
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxx
   DATABASE_URL=postgresql://...neon.tech/setu?sslmode=require
   ```
4. **Apply** → build chalega (Dockerfile auto-detect hota hai)

## Option B: Manual setup

1. **New +** → **Web Service** → apna GitHub repo select karo
2. Settings:
   | Setting | Value |
   |---|---|
   | Runtime | **Docker** (auto-detect ho jaata hai) |
   | Plan | Free (ya jo chahiye) |
   | Health Check Path | **`/health`** |
3. **Environment** tab → ye daalo:
   ```
   GOOGLE_CLIENT_ID=xxxx.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=xxxx
   DATABASE_URL=postgresql://...neon.tech/setu?sslmode=require
   ADMIN_EMAIL=you@gmail.com
   ADMIN_PASSWORD=strong-password-here
   ENV=production
   ```
   > `ADMIN_EMAIL`/`ADMIN_PASSWORD` frontend ke `/admin` panel ka login hai —
   > set nahi karoge to admin routes 503 dete hain (panel band).
   > `PUBLIC_BASE_URL` aur `PORT` **mat daalo** — Render khud
   > `RENDER_EXTERNAL_HOSTNAME` aur `PORT` inject karta hai, aur
   > `remote/config.py` dono utha leta hai.
4. **Create Web Service** → domain milega: `https://setu-xxxx.onrender.com`

---

## Google Console mein redirect URI add karo

Deploy hone ke baad jo domain mila, usse
[console.cloud.google.com/auth/clients](https://console.cloud.google.com/auth/clients)
→ apna client → **Authorized redirect URIs** mein add karo:

```
https://setu-xxxx.onrender.com/auth/callback
```

> `redirect_uri_mismatch` aaye to URI **exactly** match karo — trailing slash,
> `http` vs `https`, sab matter karta hai.

## Verify karo ki zinda hai

```bash
curl https://setu-xxxx.onrender.com/health
```

Ye milna chahiye:

```json
{"status": "ok", "database": {"backend": "postgres", "ok": true}, "service": "setu"}
```

- `"backend": "postgres"` nahi dikha, `"sqlite"` dikha → `DATABASE_URL` set nahi
  hua. Free plan pe ye data-loss bug hai, pehle theek karo.
- `503` / `"degraded"` → database reachable nahi — `DATABASE_URL` galat hai ya
  Neon project suspended hai.

Phir connector add karo:

- **claude.ai:** Settings → Connectors → Add custom connector →
  `https://setu-xxxx.onrender.com/mcp`
- **Claude Code:**
  ```bash
  claude mcp add --transport http setu https://setu-xxxx.onrender.com/mcp
  ```

## Auto-deploy

Render by default **har `git push` pe redeploy** karta hai (Settings →
Build & Deploy → Auto-Deploy). Kuch karna nahi padta.

---

## Render free plan ki asli limits

| Limit | Matlab |
|---|---|
| **15 min idle → spin down** | Agla request ~50s lega (cold start). Claude ka pehla tool call timeout ho sakta hai — retry karne pe chal jaata hai. |
| 750 hrs/month | Ek service 24/7 ke liye kaafi hai |
| No persistent disk | Isi liye Neon Postgres zaroori hai (upar) |

Spin-down se bachna hai to:
- **Starter plan** ($7/mo) — kabhi nahi sota, ya
- Koi uptime monitor ([UptimeRobot](https://uptimerobot.com) free) har 10 min
  pe `/health` ping kare — service jagi rehti hai aur monitoring bhi mil gayi

## Troubleshooting

| Problem | Wajah |
|---|---|
| Build fail | Dockerfile repo root pe hona chahiye (hai). Render ka "Root Directory" setting khali rakho. |
| `Missing environment variables` log mein | `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` set nahi |
| claude.ai connect nahi ho raha | URL ke end mein `/mcp` lagaya? HTTPS hai? |
| Login ke baad `redirect_uri_mismatch` | Redirect URI Google Console mein add nahi kiya (upar dekho) |
| Har hafte sab users logout | Google app **Testing** mode mein hai — **Publish app** dabao ([remote/README.md](remote/README.md) § Publishing status) |
| Data gayab ho gaya | SQLite + free plan. `DATABASE_URL` set karo. |
