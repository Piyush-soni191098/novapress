from __future__ import annotations

import logging
from typing import Any

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

_BASE = "https://gnews.io/api/v4"

# GNews topic slugs
_GNEWS_TOPICS = {
    "world-news": "world",
    "politics": "nation",
    "business": "business",
    "finance": "business",
    "technology": "technology",
    "sports": "sports",
    "entertainment": "entertainment",
    "science": "science",
    "health": "health",
}


class GNewsProvider(BaseProvider):
    name = "gnews"

    async def fetch(
        self,
        query: str,
        categories: list[str],
        language: str = "en",
        country: str = "",
        page_size: int = 20,
    ) -> list[Article]:
        if not config.GNEWS_API_KEY:
            return []

        cache_key = f"gnews::{query}::{','.join(sorted(categories))}::{language}::{country}"
        cached = cache_get(cache_key, config.CACHE_TTL_SECONDS)
        if cached is not None:
            return [Article(**a) for a in cached]

        articles = await self._fetch(query, categories, language, country, page_size)
        cache_set(cache_key, [a.model_dump() for a in articles])
        return articles

    async def _fetch(
        self,
        query: str,
        categories: list[str],
        language: str,
        country: str,
        page_size: int,
    ) -> list[Article]:
        # Prefer topic endpoint for known categories, fall back to search
        gnews_topic = None
        for slug in categories:
            gnews_topic = _GNEWS_TOPICS.get(slug)
            if gnews_topic:
                break

        lang = language[:2] if language else "en"
        country_code = country[:2].lower() if country else ""

        if gnews_topic and not query:
            endpoint = f"{_BASE}/top-headlines"
            params: dict[str, Any] = {
                "apikey": config.GNEWS_API_KEY,
                "topic": gnews_topic,
                "lang": lang,
                "max": min(page_size, 10),  # GNews free tier: max 10
            }
            if country_code:
                params["country"] = country_code
        else:
            endpoint = f"{_BASE}/search"
            params = {
                "apikey": config.GNEWS_API_KEY,
                "q": query or " ".join(categories[:3]),
                "lang": lang,
                "max": min(page_size, 10),
                "sortby": "publishedAt",
            }
            if country_code:
                params["country"] = country_code

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning("GNews error: %s", exc)
            return []

        return self._parse_articles(data.get("articles", []), categories)

    def _parse_articles(
        self, raw: list[dict[str, Any]], categories: list[str]
    ) -> list[Article]:
        results: list[Article] = []
        for item in raw:
            url = (item.get("url") or "").strip()
            title = clean_html(item.get("title") or "")
            if not url or not title:
                continue
            source_info = item.get("source") or {}
            source = source_info.get("name") or source_from_url(url)
            results.append(
                Article(
                    id=url,
                    title=title,
                    description=clean_html(item.get("description") or "")[:500],
                    url=url,
                    image_url=item.get("image"),
                    source=source,
                    published_at=parse_date(item.get("publishedAt")),
                    categories=categories,
                    provider=self.name,
                )
            )
        return results
