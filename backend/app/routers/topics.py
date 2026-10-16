from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.services.feed import get_topic_feed

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("/{topic_slug}/news")
async def topic_news(
    topic_slug: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=60),
    language: str = Query(default="en"),
    location: str = Query(default="", max_length=80),
) -> dict[str, Any]:
    return await get_topic_feed(
        topic_slug=topic_slug,
        language=language,
        country=location,
        page=page,
        page_size=page_size,
    )
