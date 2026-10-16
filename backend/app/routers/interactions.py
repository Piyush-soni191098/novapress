from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth import get_current_user, get_user_id
from app.database import get_supabase_admin
from app.models import BatchInteractionRequest, InteractionEvent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/interactions", tags=["interactions"])

_MAX_BATCH = 50


def _row_from_event(uid: str, event: InteractionEvent) -> dict:
    return {
        "user_id": uid,
        "article_id": event.article_id,
        "article_url": event.article_url,
        "event_type": event.event_type,
        "topic_slug": event.topic_slug,
        "provider": event.provider,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _feedback_row_from_event(uid: str, event: InteractionEvent) -> dict | None:
    feedback_types = {"like", "dislike", "more_like_this", "less_like_this", "hide"}
    if event.event_type not in feedback_types:
        return None
    return {
        "user_id": uid,
        "article_id": event.article_id,
        "feedback_type": event.event_type,
        "topic_slug": event.topic_slug,
    }


async def _persist_events(uid: str, events: list[InteractionEvent]) -> None:
    db = get_supabase_admin()
    if not db:
        return
    rows = [_row_from_event(uid, e) for e in events]
    feedback_rows = [
        r for e in events if (r := _feedback_row_from_event(uid, e)) is not None
    ]
    try:
        db.table("user_interactions").insert(rows).execute()
        if feedback_rows:
            db.table("user_feedback").upsert(
                feedback_rows, on_conflict="user_id,article_id,feedback_type"
            ).execute()
    except Exception as exc:
        logger.warning("Failed to persist interactions: %s", exc)


@router.post("", status_code=202)
async def record_interaction(
    event: InteractionEvent,
    user: dict = Depends(get_current_user),
) -> dict[str, str]:
    uid = get_user_id(user)
    await _persist_events(uid, [event])
    return {"status": "accepted"}


@router.post("/batch", status_code=202)
async def record_interactions_batch(
    payload: BatchInteractionRequest,
    user: dict = Depends(get_current_user),
) -> dict[str, Any]:
    if len(payload.events) > _MAX_BATCH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Too many events in batch (max {_MAX_BATCH})",
        )
    uid = get_user_id(user)
    await _persist_events(uid, payload.events)
    return {"status": "accepted", "count": len(payload.events)}
