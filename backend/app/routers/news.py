from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Query

from app.providers.selector import fetch_for_interests
from app.services.categories import get_query_for_slugs

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
async def get_news(
    categories: str = Query(default="technology", description="Comma-separated category slugs"),
    query: str = Query(default="", max_length=200),
    language: str = Query(default="en", max_length=10),
    location: str = Query(default="", max_length=80),
    limit: int = Query(default=30, ge=1, le=60),
) -> dict[str, Any]:
    slugs = [s.strip().lower() for s in categories.split(",") if s.strip()]
    if not slugs:
        slugs = ["technology"]

    search_query = query.strip() or get_query_for_slugs(slugs[:5])

    articles = await fetch_for_interests(
        interest_slugs=slugs,
        query=search_query,
        language=language,
        country=location,
        page_size_per_provider=limit,
    )

    return {
        "articles": [a.model_dump() for a in articles[:limit]],
        "count": min(len(articles), limit),
        "categories": slugs,
        "location": location,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "notice": "Headlines and descriptions are supplied by external sources. Open the original article for full context.",
    }


@router.get("/search")
async def search_news(
    q: str = Query(..., min_length=2, max_length=200),
    language: str = Query(default="en", max_length=10),
    location: str = Query(default="", max_length=80),
    limit: int = Query(default=30, ge=1, le=60),
) -> dict[str, Any]:
    articles = await fetch_for_interests(
        interest_slugs=[],
        query=q.strip(),
        language=language,
        country=location,
        page_size_per_provider=limit,
    )
    return {
        "articles": [a.model_dump() for a in articles[:limit]],
        "count": min(len(articles), limit),
        "query": q,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
