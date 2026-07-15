# Setu — Frontend

Next.js 15 (App Router) + Tailwind 4. Landing page, developer connect docs, aur
dashboard.

```bash
npm install
cp .env.local.example .env.local     # NEXT_PUBLIC_SETU_URL bharo
npm run dev                          # http://localhost:3000
```

## Pages

| Route | Kya hai |
|---|---|
| `/` | Landing — Setu kya hai, flow, aur "inbox padh nahi sakta" wali baat |
| `/connect` | Developer docs — Claude / ChatGPT / Claude Code setup, tools, limits, troubleshooting |
| `/dashboard` | Stats: sent, delivery rate, quota meter, recent sends |

## Env

```env
NEXT_PUBLIC_SETU_URL=https://setu-production.up.railway.app
```

Ye do jagah use hota hai: `/connect` pe dikhne wala connector URL, aur dashboard
ka API origin. Set nahi kiya to `http://localhost:8000` maan leta hai.

## Deploy

**Vercel yahan sahi jagah hai** — ye static/SSR frontend hai, wahi Vercel ka kaam
hai. (MCP *server* Vercel pe nahi ja sakta — kyun, wo `../remote/README.md` mein
likha hai.)

```bash
vercel
```

Vercel pe `NEXT_PUBLIC_SETU_URL` env var set karna. Phir server pe
`FRONTEND_ORIGIN` apne Vercel domain pe set karna, warna dashboard ki API call
CORS pe block hogi.

## Dashboard ka auth — ye abhi adhoora hai

Dashboard `GET /api/stats` se padhta hai aur `sessionStorage` mein
`setu_token` (Google access token) dhundhta hai. **Web pe Google sign-in abhi
wire nahi hua** — isliye abhi dashboard hamesha "Connect Setu" wala empty state
dikhayega.

Poora karne ke liye: Google sign-in add karo (NextAuth ya Google Identity
Services), `openid` + `email` scope maango, aur mile hue access token ko
`sessionStorage.setItem("setu_token", token)` kar do. Server side ready hai —
`/api/stats` token ko khud identity mein resolve karta hai, to har user sirf
apna data dekh payega.

## Design

Colors data-viz reference palette se hain — contrast aur colorblind-safety ke
liye pre-validated. Light aur dark dono **chune gaye** hain (dark light ka
automatic flip nahi hai), `app/globals.css` mein.

Kuch rules jo todna nahi:

- **Status kabhi color-alone nahi** — har success/failure ke saath icon + label
  jaata hai, taaki colorblind users ko bhi dikhe
- **Ek hero figure per view** (dashboard pe "Applications sent")
- **`tabular-nums` sirf columns mein** — bade standalone numbers proportional
  figures use karte hain, warna `121` jaisa number display size pe dhila lagta hai
- **Wide content apne container mein scroll kare** (`.scroll-x`) — page body kabhi
  horizontally scroll na kare
