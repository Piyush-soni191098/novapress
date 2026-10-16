from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user, get_user_id
from app.database import get_supabase_admin
from app.models import OnboardingData, PreferencesUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/preferences", tags=["preferences"])


def _require_db():
    db = get_supabase_admin()
    if not db:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured.",
        )
    return db


@router.get("")
async def get_preferences(user: dict = Depends(get_current_user)) -> dict[str, Any]:
    db = _require_db()
    uid = get_user_id(user)
    try:
        pref = db.table("user_preferences").select("*").eq("user_id", uid).maybe_single().execute()
        interests_r = db.table("user_interests").select("*").eq("user_id", uid).execute()
        profile_r = db.table("profiles").select("*").eq("id", uid).maybe_single().execute()
        return {
            "preferences": pref.data or {},
            "interests": interests_r.data or [],
            "profile": profile_r.data or {},
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("")
async def update_preferences(
    payload: PreferencesUpdate,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    db = _require_db()
    uid = get_user_id(user)
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    updates["user_id"] = uid
    try:
        r = db.table("user_preferences").upsert(updates, on_conflict="user_id").execute()
        return {"preferences": (r.data or [{}])[0]}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/interests")
async def set_interests(
    interests: list[dict],
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Replace the user's full interest list. Each item: {category_slug, strength}."""
    db = _require_db()
    uid = get_user_id(user)
    try:
        db.table("user_interests").delete().eq("user_id", uid).execute()
        if interests:
            rows = [
                {
                    "user_id": uid,
                    "category_slug": i.get("category_slug", ""),
                    "strength": float(i.get("strength", 1.0)),
                }
                for i in interests
                if i.get("category_slug")
            ]
            if rows:
                db.table("user_interests").insert(rows).execute()
        return {"count": len(interests)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/onboarding")
async def save_onboarding(
    payload: OnboardingData,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    """Save onboarding data in one shot."""
    db = _require_db()
    uid = get_user_id(user)
    try:
        # Profile — graceful: if the column doesn't exist yet, skip rather than failing
        # Run the SQL migration to add display_name/onboarding_complete columns if needed.
        try:
            profile_data: dict = {"id": uid, "onboarding_complete": True}
            if payload.display_name:
                profile_data["display_name"] = payload.display_name
            db.table("profiles").upsert(profile_data, on_conflict="id").execute()
        except Exception as profile_err:
            logger.warning("Profile upsert skipped (missing columns?): %s — run SQL migration", profile_err)
        # Interests
        db.table("user_interests").delete().eq("user_id", uid).execute()
        if payload.interests:
            rows = [
                {"user_id": uid, "category_slug": slug, "strength": 1.0}
                for slug in payload.interests
            ]
            db.table("user_interests").insert(rows).execute()
        # Preferences
        db.table("user_preferences").upsert(
            {
                "user_id": uid,
                "language": payload.language,
                "country": payload.country,
                "muted_topics": payload.muted_topics,
                "preferred_publishers": payload.preferred_publishers,
                "tracking_enabled": payload.tracking_enabled,
            },
            on_conflict="user_id",
        ).execute()
        return {"status": "saved"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
