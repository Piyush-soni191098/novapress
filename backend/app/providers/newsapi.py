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

_BASE = "https://newsapi.org/v2"

# Maps internal category slugs to NewsAPI category names.
_NEWSAPI_CATEGORIES = {
    "technology": "technology",
    "science": "science",
    "health": "health",
    "sports": "sports",
    "entertainment": "entertainment",
    "business": "business",
    "finance": "business",
    "politics": "general",
    "world-news": "general",
}


class NewsAPIProvider(BaseProvider):
    name = "newsapi"

    async def fetch(
        self,
        query: str,
        categories: list[str],
        language: str = "en",
        country: str = "",
        page_size: int = 20,
    ) -> list[Article]:
        if not config.NEWSAPI_API_KEY:
            return []

        cache_key = f"newsapi::{query}::{','.join(sorted(categories))}::{language}"
        cached = cache_get(cache_key, config.CACHE_TTL_SECONDS)
        if cached is not None:
            return [Article(**a) for a in cached]

        articles = await self._fetch_everything(query, categories, language, page_size)
        if not articles:
            articles = await self._fetch_top_headlines(categories, language, country, page_size)

        data = [a.model_dump() for a in articles]
        cache_set(cache_key, data)
        return articles

    async def _fetch_everything(
        self, query: str, categories: list[str], language: str, page_size: int
    ) -> list[Article]:
        if not query:
            return []
        params: dict[str, Any] = {
            "apiKey": config.NEWSAPI_API_KEY,
            "q": query,
            "language": language,
            "sortBy": "publishedAt",
            "pageSize": min(page_size, 100),
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{_BASE}/everything", params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning("NewsAPI everything error: %s", exc)
            return []

        return self._parse_articles(data.get("articles", []), categories)

    async def _fetch_top_headlines(
        self,
        categories: list[str],
        language: str,
        country: str,
        page_size: int,
    ) -> list[Article]:
        newsapi_cat = None
        for slug in categories:
            newsapi_cat = _NEWSAPI_CATEGORIES.get(slug)
            if newsapi_cat:
                break

        params: dict[str, Any] = {
            "apiKey": config.NEWSAPI_API_KEY,
            "language": language,
            "pageSize": min(page_size, 100),
        }
        if newsapi_cat:
            params["category"] = newsapi_cat
        if country:
            params["country"] = country.lower()[:2]

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{_BASE}/top-headlines", params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning("NewsAPI top-headlines error: %s", exc)
            return []

        return self._parse_articles(data.get("articles", []), categories)

    def _parse_articles(
        self, raw: list[dict[str, Any]], categories: list[str]
    ) -> list[Article]:
        results: list[Article] = []
        for item in raw:
            url = (item.get("url") or "").strip()
            title = clean_html(item.get("title") or "")
            if not url or not title or url == "https://removed.com":
                continue
            source_info = item.get("source") or {}
            source = source_info.get("name") or source_from_url(url)
            results.append(
                Article(
                    id=url,
                    title=title,
                    description=clean_html(item.get("description") or "")[:500],
                    url=url,
                    image_url=item.get("urlToImage"),
                    source=source,
                    author=item.get("author"),
                    published_at=parse_date(item.get("publishedAt")),
                    categories=categories,
                    provider=self.name,
                )
            )
        return results
