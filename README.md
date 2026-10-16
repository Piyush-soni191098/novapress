# Signal — Personalized News PWA

A full-featured, multi-user news intelligence platform. Aggregates headlines from NewsAPI, GNews, and Marketaux, ranks them with a weighted recommendation engine, and serves a personalized feed via a PWA frontend backed by FastAPI and Supabase.

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Frontend (Vanilla HTML/CSS/JS PWA)      │
│  login · register · onboarding           │
│  dashboard · discover · bookmarks        │
│  insights · settings                     │
└────────────────────┬────────────────────┘
                     │ REST (JSON)
┌────────────────────▼────────────────────┐
│  FastAPI backend  (Python 3.10+)         │
│  /api/feed  /api/news  /api/bookmarks    │
│  /api/interactions  /api/preferences     │
│  /api/insights  /api/categories          │
│                                          │
│  Providers:  NewsAPI · GNews · Marketaux │
│              Google News RSS (fallback)  │
│  Services:   ranking · categories · feed │
└────────────────────┬────────────────────┘
                     │ Supabase SDK
┌────────────────────▼────────────────────┐
│  Supabase (PostgreSQL + Auth)            │
│  profiles · user_interests               │
│  bookmarks · user_interactions           │
│  user_feedback · user_preferences       │
└─────────────────────────────────────────┘
```

---

## Prerequisites

- Python 3.10 or later
- A Supabase project (free tier is fine): <https://supabase.com>
- API keys for at least one news provider (all three are recommended)

---

## Folder structure

```
personalized_news_pwa_starter/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI app, CORS, router registration
│   │   ├── config.py          # Env-var loader
│   │   ├── database.py        # Supabase client helpers
│   │   ├── auth.py            # JWT verification dependency
│   │   ├── models.py          # Pydantic models
│   │   ├── providers/         # NewsAPI, GNews, Marketaux, RSS, selector
│   │   ├── routers/           # health, news, feed, bookmarks, …
│   │   └── services/          # categories, ranking, feed
│   ├── tests/
│   │   └── test_providers.py  # 33 unit tests
│   ├── requirements.txt
│   ├── pytest.ini
│   └── .env                   # your secrets (never committed)
├── frontend/
│   ├── index.html             # landing page
│   ├── login.html
│   ├── register.html
│   ├── forgot-password.html
│   ├── reset-password.html
│   ├── onboarding.html
│   ├── dashboard.html
│   ├── discover.html
│   ├── bookmarks.html
│   ├── insights.html
│   ├── settings.html
│   ├── config.js              # ← fill in your Supabase URL + anon key
│   ├── styles.css
│   ├── sw.js                  # service worker (never caches auth requests)
│   ├── manifest.webmanifest
│   └── js/
│       ├── auth.js            # Supabase auth wrapper
│       ├── api.js             # backend API client
│       ├── components.js      # article cards, interactions
│       └── utils.js           # shared helpers
└── migrations/
    ├── 001_initial_schema.sql # tables and indexes
    └── 002_rls_policies.sql   # Row Level Security + auto-profile trigger
```

---

## 1 — Clone and install backend dependencies

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 2 — Set environment variables

Open `backend/.env` (create it if missing — use `.env.example` as a template):

```dotenv
# News providers
NEWSAPI_API_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_key
MARKETAUX_API_TOKEN=your_marketaux_token

# Supabase
SUPABASE_URL=https://xxxxxxxxxxxxxxxxxxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...   # anon/public key
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...  # service-role key (backend only)

# Optional
ENVIRONMENT=development
CACHE_TTL_SECONDS=300
FRONTEND_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

**Where to find Supabase keys:** Supabase dashboard → Settings → API.

> **Security rule:** `SUPABASE_SERVICE_ROLE_KEY` is only used by the backend. It must never appear in `frontend/config.js` or any client-side file.

---

## 3 — Run SQL migrations

In the Supabase dashboard open **SQL Editor** and run each file in order:

1. `migrations/001_initial_schema.sql` — creates tables, indexes, trigger function
2. `migrations/002_rls_policies.sql` — enables RLS and creates all policies

---

## 4 — Configure Supabase Auth redirect URLs

In the Supabase dashboard → **Authentication → URL Configuration**:

| Setting | Value (development) |
|---|---|
| Site URL | `http://localhost:5500` |
| Redirect URLs | `http://localhost:5500/onboarding.html` |
| | `http://localhost:5500/reset-password.html` |

For production replace `localhost:5500` with your deployed domain.

Optionally configure a custom SMTP server under **Authentication → SMTP Settings** so verification and reset emails come from your own domain.

---

## 5 — Configure the frontend

Open `frontend/config.js` and fill in your values:

```javascript
window.NEWS_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8000",   // backend URL
  SUPABASE_URL: "https://xxxx.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGci...",         // anon/public key only
};
```

---

## 6 — Start the backend

```bash
cd backend
uvicorn app.main:app --reload
```

The API is now at `http://127.0.0.1:8000`. Visit `http://127.0.0.1:8000/docs` for the interactive OpenAPI docs.

Health check:

```
GET http://127.0.0.1:8000/health
→ {"status":"ok","providers":{"newsapi":true,"gnews":true,"marketaux":true,"rss":true},"supabase":true}
```

---

## 7 — Serve the frontend

Any static file server works. With the VS Code **Live Server** extension open `frontend/index.html` (default port 5500). Alternatively:

```bash
cd frontend
python -m http.server 5500
```

Then open `http://localhost:5500` in your browser.

---

## API reference

All authenticated routes require `Authorization: Bearer <jwt>` where `<jwt>` is the Supabase session access token.

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Provider and Supabase status |
| GET | `/api/categories` | — | All categories (`?q=` to search) |
| GET | `/api/news` | optional | Headlines (`?q=`, `?topics=`, `?page=`, `?page_size=`) |
| GET | `/api/news/search` | optional | Full-text search (`?q=`) |
| GET | `/api/topics/{slug}/news` | optional | Articles for one topic |
| GET | `/api/feed/for-you` | required | Personalized ranked feed |
| GET | `/api/feed/latest` | required | Chronological feed |
| GET | `/api/feed/following` | required | Feed for followed interests only |
| GET | `/api/bookmarks` | required | Saved articles |
| POST | `/api/bookmarks` | required | Save an article |
| DELETE | `/api/bookmarks/{article_id}` | required | Remove bookmark |
| POST | `/api/interactions` | optional | Record single event |
| POST | `/api/interactions/batch` | optional | Record up to 50 events |
| GET | `/api/preferences` | required | Load user preferences |
| PUT | `/api/preferences` | required | Update preferences |
| POST | `/api/preferences/interests` | required | Set followed categories |
| POST | `/api/preferences/onboarding` | required | Complete onboarding |
| GET | `/api/insights` | required | Reading stats |

---

## Running tests

```bash
cd backend
pytest -v
```

All 33 tests cover article normalization, URL/title deduplication, category taxonomy, recommendation scoring, freshness ranking, diversity capping, and interaction event validation.

---

## Troubleshooting

**`supabase: false` in health check**
Add `SUPABASE_URL` and `SUPABASE_ANON_KEY` to `backend/.env` and restart uvicorn.

**Port 8000 already in use**
A previous uvicorn process is running. Kill it or use `--port 8001` and update `API_BASE_URL` in `frontend/config.js`.

**CORS errors in browser**
Add your frontend origin to `FRONTEND_ORIGINS` in `backend/.env`.

**Email verification link not working**
Confirm the redirect URL in Supabase Auth settings matches the URL you are serving the frontend from (including port).

**Free tier rate limits**
- GNews: 10 articles per call, 100 requests/day
- Marketaux: 3 articles per call, 100 requests/day
- NewsAPI: 100 requests/day (developer plan)

The RSS fallback (Google News) is unlimited and always active.

---

## Deployment

For production:

1. Deploy the FastAPI backend to any host that runs Python (Fly.io, Railway, Render, etc.). Set all environment variables in the host's secret manager.
2. Set `ENVIRONMENT=production` in env vars.
3. Deploy the `frontend/` directory to any static host (Netlify, Vercel, Cloudflare Pages, etc.).
4. Update `frontend/config.js` → `API_BASE_URL` to your backend's public URL.
5. Update Supabase Auth redirect URLs to your production domain.
6. Add your production frontend origin to `FRONTEND_ORIGINS`.
