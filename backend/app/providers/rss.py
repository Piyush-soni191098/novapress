from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote_plus

import feedparser
import httpx

from app import config
from app.models import Article
from app.providers.base import (
    BaseProvider,
    cache_get,
    cache_set,
    clean_html,
    parse_date,
    source_from_url,
)

logger = logging.getLogger(__name__)


class RSSProvider(BaseProvider):
    name = "rss"

    async def fetch(
        self,
        query: str,
        categories: list[str],
        language: str = "en",
        country: str = "",
        page_size: int = 20,
    ) -> list[Article]:
        cache_key = f"rss::{query}::{','.join(sorted(categories))}::{country}"
        cached = cache_get(cache_key, config.CACHE_TTL_SECONDS)
        if cached is not None:
            return [Article(**a) for a in cached]

        articles = await self._fetch(query, categories, country, page_size)
        cache_set(cache_key, [a.model_dump() for a in articles])
        return articles

    async def _fetch(
        self,
        query: str,
        categories: list[str],
        country: str,
        page_size: int,
    ) -> list[Article]:
        if not query:
            query = " OR ".join(categories[:3]) if categories else "news"

        combined = query
        if country.strip():
            combined += f' "{country.strip()}"'
        q = quote_plus(combined)
        url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"

        try:
            async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
                response = await client.get(
                    url, headers={"User-Agent": "PersonalizedNewsPWA/2.0"}
                )
                response.raise_for_status()
                parsed = feedparser.parse(response.text)
        except Exception as exc:
            logger.warning("RSS fetch error: %s", exc)
            return []

        results: list[Article] = []
        for entry in parsed.entries[: min(page_size, 25)]:
            link = getattr(entry, "link", "")
            title = clean_html(getattr(entry, "title", ""))
            if not link or not title:
                continue
            summary = clean_html(getattr(entry, "summary", ""))
            source_obj = getattr(entry, "source", {})
            source_name = (
                source_obj.get("title", "") if isinstance(source_obj, dict) else ""
            )
            results.append(
                Article(
                    id=link,
                    title=title,
                    description=summary[:500],
                    url=link,
                    source=source_from_url(link, source_name),
                    published_at=parse_date(
                        getattr(entry, "published", None)
                        or getattr(entry, "updated", None)
                    ),
                    categories=categories,
                    provider=self.name,
                )
            )
        return results
