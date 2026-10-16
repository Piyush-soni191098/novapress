<div align="center">

<img src="frontend/logo.svg" alt="NovaPress Logo" width="320"/>

# NovaPress

### Less noise. More signal.

**A personalized news intelligence platform built for the modern reader.**  
Your interests. Your region. The stories worth your time — ranked, filtered, and delivered beautifully.

<br/>

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![PWA](https://img.shields.io/badge/PWA-5A0FC8?style=for-the-badge&logo=pwa&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

</div>

---

## What is NovaPress?

Most news apps give you everything. NovaPress gives you *your* everything.

It pulls headlines from **3 live news providers** — NewsAPI, GNews, and Marketaux — deduplicates them, scores each article against your reading history and interests, and surfaces what actually matters to you. The more you use it, the smarter it gets.

No algorithm you can't control. No dark patterns. Just clean, fast, personalized news.

---

## ✨ Features

- 🧠 **Adaptive feed** — learns from every article you read, like, or mute
- 📰 **3 live providers** — NewsAPI · GNews · Marketaux + Google News RSS fallback
- 🗂️ **30+ categories** — Technology, Finance, Cricket, Science, Entertainment and more
- 🔖 **Bookmarks** — save articles to read later, accessible across devices
- 📊 **Reading Insights** — see your reading patterns and top topics at a glance
- 📱 **PWA** — install it on your phone or desktop, works offline
- 🔐 **Full auth flow** — sign up, email verification, forgot password, reset password
- ⚙️ **Settings** — language, region, personalization tracking toggle

---

## 🏗️ How it's built

```
┌──────────────────────────────────────────┐
│           Frontend  (PWA)                 │
│   Vanilla HTML · CSS · JavaScript         │
│   11 pages · Service Worker · Manifest    │
└─────────────────┬────────────────────────┘
                  │  REST / JSON
┌─────────────────▼────────────────────────┐
│           FastAPI  (Python)               │
│   Personalized feed · News aggregation    │
│   Bookmarks · Interactions · Insights     │
└─────────────────┬────────────────────────┘
                  │  Supabase SDK
┌─────────────────▼────────────────────────┐
│           Supabase                        │
│   PostgreSQL · Auth · Row Level Security  │
└──────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
novapress/
│
├── 📂 backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── auth.py              # JWT verification
│   │   ├── config.py            # Environment loader
│   │   ├── database.py          # Supabase client
│   │   ├── models.py            # Pydantic models
│   │   ├── providers/           # NewsAPI · GNews · Marketaux · RSS
│   │   ├── routers/             # All API route handlers
│   │   └── services/            # Feed ranking · categories · composition
│   ├── tests/                   # 33 unit tests
│   ├── requirements.txt
│   └── .env.example             # ← copy this to .env
│
├── 📂 frontend/
│   ├── index.html               # Landing page
│   ├── dashboard.html           # Main feed
│   ├── discover.html            # Browse categories
│   ├── bookmarks.html
│   ├── insights.html
│   ├── settings.html
│   ├── login / register / onboarding / reset-password
│   ├── logo.svg                 # NovaPress brand logo
│   ├── styles.css               # Single unified stylesheet
│   ├── sw.js                    # Service worker
│   └── js/
│       ├── auth.js              # Supabase auth wrapper
│       ├── api.js               # Backend API client
│       ├── components.js        # Article cards · interactions
│       └── utils.js             # Shared helpers
│
└── 📂 migrations/
    ├── 001_initial_schema.sql   # Tables · indexes · triggers
    └── 002_rls_policies.sql     # Row Level Security policies
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- A free [Supabase](https://supabase.com) project
- At least one news API key (all three recommended):
  - [NewsAPI](https://newsapi.org) — free developer plan
  - [GNews](https://gnews.io) — free tier available
  - [Marketaux](https://www.marketaux.com) — free tier available

---

### 1. Clone the repository

```bash
git clone https://github.com/Piyush-soni191098/novapress.git
cd novapress
```

### 2. Set up the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure your environment

```bash
cp .env.example .env
```

Open `backend/.env` and fill in your keys:

```dotenv
# ── News Providers ────────────────────────────
NEWSAPI_API_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_key
MARKETAUX_API_TOKEN=your_marketaux_token

# ── Supabase ──────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...   # backend only — never expose this

# ── Optional ──────────────────────────────────
ENVIRONMENT=development
CACHE_TTL_SECONDS=300
FRONTEND_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

> 💡 Find your Supabase keys at: **Dashboard → Settings → API**

### 4. Run database migrations

In your Supabase project → **SQL Editor**, run these files in order:

```
migrations/001_initial_schema.sql   ← run first
migrations/002_rls_policies.sql     ← run second
```

### 5. Configure Supabase Auth redirect URLs

**Dashboard → Authentication → URL Configuration**

| Setting | Value |
|---|---|
| Site URL | `http://localhost:5500` |
| Redirect URLs | `http://localhost:5500/onboarding.html` |
| | `http://localhost:5500/reset-password.html` |

### 6. Configure the frontend

Open `frontend/config.js` and set your values:

```javascript
window.NEWS_CONFIG = {
  API_BASE_URL:      "http://127.0.0.1:8000",
  SUPABASE_URL:      "https://xxxx.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGci...",   // anon key only — safe for frontend
};
```

### 7. Start the backend

```bash
cd backend
uvicorn app.main:app --reload
```

The API is live at `http://127.0.0.1:8000`  
Interactive docs: `http://127.0.0.1:8000/docs`

### 8. Serve the frontend

```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500` — you're in. 🎉

---

## 🔌 API Reference

All protected routes require: `Authorization: Bearer <supabase_jwt>`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/health` | — | Check providers & Supabase status |
| `GET` | `/api/categories` | — | List all 30+ categories |
| `GET` | `/api/news` | optional | Headlines with filters (`?q=`, `?topics=`, `?page=`) |
| `GET` | `/api/news/search` | optional | Full-text search |
| `GET` | `/api/feed/for-you` | ✓ | Personalized ranked feed |
| `GET` | `/api/feed/latest` | ✓ | Chronological feed |
| `GET` | `/api/bookmarks` | ✓ | Your saved articles |
| `POST` | `/api/bookmarks` | ✓ | Save an article |
| `DELETE` | `/api/bookmarks/{id}` | ✓ | Remove a bookmark |
| `POST` | `/api/interactions` | optional | Log a reading event |
| `GET` | `/api/preferences` | ✓ | Load user preferences |
| `PUT` | `/api/preferences` | ✓ | Update preferences |
| `GET` | `/api/insights` | ✓ | Reading stats & analytics |

---

## 🧪 Tests

```bash
cd backend
pytest -v
```

33 tests covering article normalization, deduplication, recommendation scoring, freshness ranking, diversity capping, and interaction validation.

---

## 🌐 Deploying to Production

| What | Where |
|---|---|
| Backend (FastAPI) | [Render](https://render.com) · [Railway](https://railway.app) · [Fly.io](https://fly.io) |
| Frontend (static) | [Netlify](https://netlify.com) · [Vercel](https://vercel.com) · [Cloudflare Pages](https://pages.cloudflare.com) |

**Checklist before going live:**
- [ ] Set all env vars in your host's secret manager (never in code)
- [ ] Set `ENVIRONMENT=production`
- [ ] Update `frontend/config.js` → `API_BASE_URL` to your backend's public URL
- [ ] Update Supabase Auth redirect URLs to your production domain
- [ ] Add your production domain to `FRONTEND_ORIGINS`

---

## 🛠️ Troubleshooting

**`supabase: false` in health check**  
→ Check `SUPABASE_URL` and `SUPABASE_ANON_KEY` in your `.env`

**Port 8000 already in use**  
→ Run `uvicorn app.main:app --reload --port 8001` and update `API_BASE_URL` in `config.js`

**CORS errors in browser**  
→ Add your frontend origin to `FRONTEND_ORIGINS` in `.env`

**Email verification link not working**  
→ Make sure the redirect URL in Supabase Auth settings exactly matches where you're serving the frontend (including the port)

**API rate limits (free tiers)**  
- GNews: 100 requests/day
- Marketaux: 100 requests/day  
- NewsAPI: 100 requests/day  
- Google News RSS: unlimited (always active as fallback)

---

## 🤝 Contributing

Pull requests are welcome. For major changes, open an issue first to discuss what you'd like to change.

---

## 📄 License

MIT — feel free to use, modify, and distribute.

---

<div align="center">

Built with ☕ and a healthy obsession with clean news.

**[github.com/Piyush-soni191098/novapress](https://github.com/Piyush-soni191098/novapress)**

</div>
