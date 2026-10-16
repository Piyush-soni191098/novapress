from __future__ import annotations

import re
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import urlparse

from app.models import Article


def clean_html(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", value).strip()


def parse_date(raw: Any) -> str:
    if not raw:
        return ""
    if isinstance(raw, datetime):
        dt = raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    raw = str(raw).strip()
    for parser in (_try_iso, _try_rfc2822):
        result = parser(raw)
        if result:
            return result
    return raw


def _try_iso(raw: str) -> str:
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def _try_rfc2822(raw: str) -> str:
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        return ""


def source_from_url(url: str, fallback: str = "") -> str:
    try:
        host = urlparse(url).netloc.lower()
        return host.removeprefix("www.") or fallback or "News source"
    except Exception:
        return fallback or "News source"


def normalize_url(url: str) -> str:
    """Return a canonical URL key for deduplication."""
    return url.split("?")[0].rstrip("/").lower()


# Simple in-process cache shared by all providers.
_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def cache_get(key: str, ttl: int) -> list[dict[str, Any]] | None:
    entry = _CACHE.get(key)
    if entry and time.time() - entry[0] < ttl:
        return entry[1]
    return None


def cache_set(key: str, data: list[dict[str, Any]]) -> None:
    _CACHE[key] = (time.time(), data)


class BaseProvider(ABC):
    name: str = "unknown"

    @abstractmethod
    async def fetch(
        self,
        query: str,
        categories: list[str],
        language: str = "en",
        country: str = "",
        page_size: int = 20,
    ) -> list[Article]:
        ...
