from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.services.categories import get_all_categories, search_categories

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
async def list_categories(
    q: str = Query(default="", max_length=80),
) -> dict[str, Any]:
    if q.strip():
        cats = search_categories(q.strip())
    else:
        cats = get_all_categories()
    return {"categories": cats, "count": len(cats)}
