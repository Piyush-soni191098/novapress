from __future__ import annotations

import os
import sys
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        print(f"[config] WARNING: {name} is not set.", file=sys.stderr)
    return value


def _optional(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


# --- News providers ----------------------------------------------------------------
NEWSAPI_API_KEY: str = _optional("NEWSAPI_API_KEY")
GNEWS_API_KEY: str = _optional("GNEWS_API_KEY")
MARKETAUX_API_TOKEN: str = _optional("MARKETAUX_API_TOKEN")

# --- Supabase ----------------------------------------------------------------------
SUPABASE_URL: str = _optional("SUPABASE_URL")
SUPABASE_ANON_KEY: str = _optional("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY: str = _optional("SUPABASE_SERVICE_ROLE_KEY")

# --- App ---------------------------------------------------------------------------
FRONTEND_ORIGINS: list[str] = [
    o.strip()
    for o in _optional(
        "FRONTEND_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
    ).split(",")
    if o.strip()
]

ENVIRONMENT: str = _optional("ENVIRONMENT", "development")

# --- Cache / limits ----------------------------------------------------------------
CACHE_TTL_SECONDS: int = int(_optional("CACHE_TTL_SECONDS", "300"))
MAX_ARTICLES_PER_PROVIDER: int = 25
MAX_FEED_ARTICLES: int = 60


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY)


def supabase_admin_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)
