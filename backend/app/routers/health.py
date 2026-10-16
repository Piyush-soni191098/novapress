from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter

from app import config

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "providers": {
            "newsapi": bool(config.NEWSAPI_API_KEY),
            "gnews": bool(config.GNEWS_API_KEY),
            "marketaux": bool(config.MARKETAUX_API_TOKEN),
            "rss": True,
        },
        "supabase": config.supabase_configured(),
    }
