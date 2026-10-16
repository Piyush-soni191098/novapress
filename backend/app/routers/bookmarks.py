from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, get_user_id
from app.database import get_supabase_admin
from app.models import BookmarkCreate

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


def _require_db():
    db = get_supabase_admin()
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured.",
        )
    return db


@router.get("")
async def list_bookmarks(
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    db = _require_db()
    uid = get_user_id(user)
    try:
        r = db.table("bookmarks").select("*").eq("user_id", uid).order("created_at", desc=True).execute()
        return {"bookmarks": r.data or [], "count": len(r.data or [])}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("", status_code=201)
async def add_bookmark(
    payload: BookmarkCreate,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    db = _require_db()
    uid = get_user_id(user)
    row = {
        "user_id": uid,
        "article_id": payload.article_id,
        "article_url": payload.article_url,
        "title": payload.title,
        "description": payload.description,
        "image_url": payload.image_url,
        "source": payload.source,
        "published_at": payload.published_at,
        "provider": payload.provider,
        "categories": payload.categories,
    }
    try:
        r = db.table("bookmarks").upsert(row, on_conflict="user_id,article_id").execute()
        return {"bookmark": (r.data or [{}])[0]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/{article_id}", status_code=200)
async def remove_bookmark(
    article_id: str,
    user: dict = Depends(get_current_user),
) -> dict[str, str]:
    db = _require_db()
    uid = get_user_id(user)
    try:
        db.table("bookmarks").delete().eq("user_id", uid).eq("article_id", article_id).execute()
        return {"status": "deleted"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
