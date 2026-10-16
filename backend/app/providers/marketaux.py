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

_BASE = "https://api.marketaux.com/v1"

# Financial category slugs that should route through Marketaux
FINANCIAL_SLUGS = {
    "finance", "stocks", "business", "economics", "market",
    "personal-finance", "real-estate", "cryptocurrency",
}


class MarketauxProvider(BaseProvider):
    name = "marketaux"

    async def fetch(
        self,
        query: str,
        categories: list[str],
        language: str = "en",
        country: str = "",
        page_size: int = 20,
    ) -> list[Article]:
        if not config.MARKETAUX_API_TOKEN:
            return []

        # Only use Marketaux for financial topics
        financial = [s for s in categories if s in FINANCIAL_SLUGS]
        if not financial and not any(
            kw in (query or "").lower()
            for kw in ("stock", "market", "finance", "invest", "earning", "ipo")
        ):
            return []

        cache_key = f"marketaux::{query}::{','.join(sorted(categories))}::{country}"
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
        params: dict[str, Any] = {
            "api_token": config.MARKETAUX_API_TOKEN,
            "language": language[:2] if language else "en",
            "limit": min(page_size, 3),  # Free plan limit — do not increase without plan upgrade
        }
        if query:
            params["search"] = query
        if country and country.lower() in {"india", "in"}:
            params["countries"] = "in"

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(f"{_BASE}/news/all", params=params)
                response.raise_for_status()
                data = response.json()
        except Exception as exc:
            logger.warning("Marketaux error: %s", exc)
            return []

        return self._parse_articles(data.get("data", []), categories)

    def _parse_articles(
        self, raw: list[dict[str, Any]], categories: list[str]
    ) -> list[Article]:
        results: list[Article] = []
        for item in raw:
            url = (item.get("url") or "").strip()
            title = clean_html(item.get("title") or "")
            if not url or not title:
                continue

            # Extract financial entities / symbols
            entities = item.get("entities") or []
            symbols = [e.get("symbol") for e in entities if e.get("symbol")]

            results.append(
                Article(
                    id=item.get("uuid") or url,
                    title=title,
                    description=clean_html(
                        item.get("description") or item.get("snippet") or ""
                    )[:500],
                    url=url,
                    image_url=item.get("image_url"),
                    source=item.get("source") or source_from_url(url),
                    published_at=parse_date(item.get("published_at")),
                    categories=categories or ["finance"],
                    provider=self.name,
                    financial_entities=symbols,
                )
            )
        return results
