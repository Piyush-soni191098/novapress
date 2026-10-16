# NovaPress — Personalized News PWA

> Less noise. More signal. Your interests, your region, the stories worth your time.

NovaPress is a full-stack Progressive Web App that aggregates headlines from multiple news providers, ranks them with a personalized recommendation engine, and delivers a clean, fast reading experience — all backed by FastAPI and Supabase.

---

## Features

- **Personalized feed** — ranked by your reading history, liked topics, and muted sources
- **3 live news providers** — NewsAPI, GNews, Marketaux (+ Google News RSS fallback)
- **30+ categories** — Technology, Finance, Cricket, Science, Entertainment and more
- **Bookmarks & Insights** — save articles, track your reading stats
- **PWA** — installable, works offline, mobile-ready
- **Auth** — email/password sign-up, email verification, password reset via Supabase Auth

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML / CSS / JS (PWA) |
| Backend | FastAPI (Python 3.10+) |
| Database & Auth | Supabase (PostgreSQL + Row Level Security) |
| News Providers | NewsAPI · GNews · Marketaux · Google RSS |

---

## Architecture

```
┌─────────────────────────────────────────┐
│  Frontend  (PWA)                         │
│  index · login · register · onboarding  │
│  dashboard · discover · bookmarks       │
│  insights · settings                    │
└────────────────────┬────────────────────┘
                     │ REST / JSON
┌────────────────────▼────────────────────┐
│  FastAPI Backend                         │
│  /api/feed  /api/news  /api/bookmarks   │
│  /api/interactions  /api/preferences    │
│  /api/insights  /api/categories         │
└────────────────────┬────────────────────┘
                     │ Supabase SDK
┌────────────────────▼────────────────────┐
│  Supabase                                │
│  PostgreSQL · Auth · Row Level Security  │
└─────────────────────────────────────────┘
```

---

## Project Structure

```
novapress/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI entry point, CORS, router registration
│   │   ├── config.py        # Environment variable loader
│   │   ├── database.py      # Supabase client helpers
│   │   ├── auth.py          # JWT verification dependency
│   │   ├── models.py        # Pydantic request/response models
│   │   ├── providers/       # NewsAPI, GNews, Marketaux, RSS, selector
│   │   ├── routers/         # health, news, feed, bookmarks, interactions…
│   │   └── services/        # categories, ranking, feed composition
│   ├── tests/
│   │   └── test_providers.py
│   ├── requirements.txt
│   ├── .env.example         # copy to .env and fill in your keys
│   └── pytest.ini
├── frontend/
│   ├── index.html           # Landing page
│   ├── login.html
│   ├── register.html
│   ├── onboarding.html
│   ├── dashboard.html
│   ├── discover.html
│   ├── bookmarks.html
│   ├── insights.html
│   ├── settings.html
│   ├── config.js            # ← set your Supabase URL + anon key here
│   ├── styles.css
│   ├── logo.svg
│   ├── sw.js                # Service worker
│   ├── manifest.webmanifest
│   └── js/
│       ├── auth.js          # Supabase auth wrapper
│       ├── api.js           # Backend API client
│       ├── components.js    # Article cards, interactions
│       └── utils.js         # Shared helpers
└── migrations/
    ├── 001_initial_schema.sql   # Tables, indexes, trigger
    └── 002_rls_policies.sql     # Row Level Security policies
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Piyush-soni191098/novapress.git
cd novapress
```

### 2. Set up the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```dotenv
# News providers
NEWSAPI_API_KEY=your_newsapi_key
GNEWS_API_KEY=your_gnews_key
MARKETAUX_API_TOKEN=your_marketaux_token

# Supabase
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...   # backend only — never expose to frontend

# Optional
ENVIRONMENT=development
CACHE_TTL_SECONDS=300
FRONTEND_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
```

> Supabase keys: Dashboard → Settings → API

### 4. Run SQL migrations

In Supabase → **SQL Editor**, run in order:

1. `migrations/001_initial_schema.sql`
2. `migrations/002_rls_policies.sql`

### 5. Configure Supabase Auth redirect URLs

Dashboard → **Authentication → URL Configuration**

| Setting | Value |
|---|---|
| Site URL | `http://localhost:5500` |
| Redirect URLs | `http://localhost:5500/onboarding.html` |
| | `http://localhost:5500/reset-password.html` |

### 6. Configure the frontend

Open `frontend/config.js`:

```javascript
window.NEWS_CONFIG = {
  API_BASE_URL: "http://127.0.0.1:8000",
  SUPABASE_URL: "https://xxxx.supabase.co",
  SUPABASE_ANON_KEY: "eyJhbGci...",   // anon key only
};
```

### 7. Start the backend

```bash
cd backend
uvicorn app.main:app --reload
```

API runs at `http://127.0.0.1:8000` — interactive docs at `/docs`

### 8. Serve the frontend

```bash
cd frontend
python -m http.server 5500
```

Open `http://localhost:5500`

---

## API Reference

All authenticated routes require `Authorization: Bearer <jwt>` (Supabase session token).

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Provider & Supabase status |
| GET | `/api/categories` | — | All categories |
| GET | `/api/news` | optional | Headlines with filters |
| GET | `/api/news/search` | optional | Full-text search |
| GET | `/api/feed/for-you` | required | Personalized ranked feed |
| GET | `/api/feed/latest` | required | Chronological feed |
| GET | `/api/bookmarks` | required | Saved articles |
| POST | `/api/bookmarks` | required | Save an article |
| DELETE | `/api/bookmarks/{id}` | required | Remove bookmark |
| POST | `/api/interactions` | optional | Record a reading event |
| GET | `/api/preferences` | required | Load user preferences |
| PUT | `/api/preferences` | required | Update preferences |
| GET | `/api/insights` | required | Reading stats |

---

## Running Tests

```bash
cd backend
pytest -v
```

33 tests covering article normalization, deduplication, recommendation scoring, freshness ranking, and interaction validation.

---

## Deployment

1. Deploy `backend/` to any Python host (Render, Railway, Fly.io) — set all env vars in the host's secret manager
2. Deploy `frontend/` to any static host (Netlify, Vercel, Cloudflare Pages)
3. Update `frontend/config.js` → `API_BASE_URL` to your backend's public URL
4. Update Supabase Auth redirect URLs to your production domain
5. Add your production origin to `FRONTEND_ORIGINS`

---

## License

MIT
