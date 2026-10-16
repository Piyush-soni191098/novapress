from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.auth import get_current_user, get_optional_user, get_user_id
from app.services.feed import get_personalized_feed, get_topic_feed

router = APIRouter(prefix="/api/feed", tags=["feed"])


def _get_user_context(user: dict) -> dict:
    """Pull preference data from Supabase for a given user."""
    from app.database import get_supabase_admin
    admin = get_supabase_admin()
    interests: list[str] = []
    positive_categories: set[str] = set()
    negative_categories: set[str] = set()
    liked_sources: set[str] = set()
    disliked_sources: set[str] = set()

    if not admin:
        return {
            "interests": interests,
            "positive_categories": positive_categories,
            "negative_categories": negative_categories,
            "liked_sources": liked_sources,
            "disliked_sources": disliked_sources,
        }

    uid = get_user_id(user)
    try:
        r = admin.table("user_interests").select("category_slug,strength").eq("user_id", uid).execute()
        for row in (r.data or []):
            slug = row.get("category_slug", "")
            strength = float(row.get("strength", 1.0))
            if slug:
                interests.append(slug)
                if strength >= 1.5:
                    positive_categories.add(slug)
                elif strength <= 0.3:
                    negative_categories.add(slug)
    except Exception:
        pass

    try:
        r2 = admin.table("user_feedback").select("article_id,feedback_type,topic_slug,publisher").eq("user_id", uid).limit(200).execute()
        for row in (r2.data or []):
            ft = row.get("feedback_type", "")
            topic = row.get("topic_slug", "")
            pub = (row.get("publisher") or "").lower()
            if ft in {"like", "more_like_this"} and topic:
                positive_categories.add(topic)
            elif ft in {"dislike", "less_like_this"} and topic:
                negative_categories.add(topic)
            if ft == "like" and pub:
                liked_sources.add(pub)
            elif ft == "dislike" and pub:
                disliked_sources.add(pub)
    except Exception:
        pass

    return {
        "interests": interests,
        "positive_categories": positive_categories,
        "negative_categories": negative_categories,
        "liked_sources": liked_sources,
        "disliked_sources": disliked_sources,
    }


@router.get("/for-you")
async def feed_for_you(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=60),
    language: str = Query(default="en", max_length=10),
    location: str = Query(default="", max_length=80),
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    ctx = _get_user_context(user)
    return await get_personalized_feed(
        interest_slugs=ctx["interests"],
        mode="for_you",
        language=language,
        country=location,
        page=page,
        page_size=page_size,
        positive_categories=ctx["positive_categories"],
        negative_categories=ctx["negative_categories"],
        liked_sources=ctx["liked_sources"],
        disliked_sources=ctx["disliked_sources"],
    )


@router.get("/latest")
async def feed_latest(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=60),
    categories: str = Query(default="technology,world-news"),
    language: str = Query(default="en", max_length=10),
    location: str = Query(default="", max_length=80),
    user: Optional[dict] = Depends(get_optional_user),
) -> dict[str, Any]:
    slugs = [s.strip() for s in categories.split(",") if s.strip()]
    return await get_personalized_feed(
        interest_slugs=slugs,
        mode="latest",
        language=language,
        country=location,
        page=page,
        page_size=page_size,
    )


@router.get("/following")
async def feed_following(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=60),
    language: str = Query(default="en", max_length=10),
    location: str = Query(default="", max_length=80),
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    ctx = _get_user_context(user)
    # Following mode: only show interests with strength >= 1.0
    followed = [s for s in ctx["interests"] if s not in ctx["negative_categories"]]
    return await get_personalized_feed(
        interest_slugs=followed or ctx["interests"],
        mode="for_you",
        language=language,
        country=location,
        page=page,
        page_size=page_size,
        positive_categories=ctx["positive_categories"],
        negative_categories=ctx["negative_categories"],
        liked_sources=ctx["liked_sources"],
        disliked_sources=ctx["disliked_sources"],
    )
