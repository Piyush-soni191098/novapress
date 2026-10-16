from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, get_user_id
from app.database import get_supabase_admin

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("")
async def get_insights(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    db = get_supabase_admin()
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured.",
        )
    uid = get_user_id(user)

    try:
        interactions_r = (
            db.table("user_interactions")
            .select("event_type,topic_slug,created_at")
            .eq("user_id", uid)
            .order("created_at", desc=True)
            .limit(500)
            .execute()
        )
        interactions = interactions_r.data or []

        bookmarks_r = (
            db.table("bookmarks")
            .select("categories,created_at")
            .eq("user_id", uid)
            .execute()
        )
        bookmarks = bookmarks_r.data or []

        interests_r = (
            db.table("user_interests")
            .select("category_slug,strength")
            .eq("user_id", uid)
            .execute()
        )
        interests = interests_r.data or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    # Topic click counts
    topic_clicks = Counter(
        row["topic_slug"]
        for row in interactions
        if row.get("event_type") == "click" and row.get("topic_slug")
    )

    # Bookmark category frequency
    bookmark_cats = Counter()
    for bm in bookmarks:
        for cat in bm.get("categories") or []:
            bookmark_cats[cat] += 1

    # Activity over last 7 days (by day)
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    day_counts: dict[str, int] = {}
    for row in interactions:
        try:
            ts = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
            day_label = ts.strftime("%Y-%m-%d")
            day_counts[day_label] = day_counts.get(day_label, 0) + 1
        except Exception:
            pass

    return {
        "total_interactions": len(interactions),
        "total_bookmarks": len(bookmarks),
        "followed_topics": [
            {"slug": r["category_slug"], "strength": r["strength"]}
            for r in interests
        ],
        "top_clicked_topics": topic_clicks.most_common(10),
        "top_bookmarked_categories": bookmark_cats.most_common(10),
        "daily_activity": sorted(day_counts.items()),
        "data_note": "Activity shown here is based on your in-app interactions only.",
    }
