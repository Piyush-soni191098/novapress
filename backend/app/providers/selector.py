from __future__ import annotations

import asyncio
import logging
from typing import Any

from app.models import Article
from app.providers.base import normalize_url
from app.providers.gnews import GNewsProvider
from app.providers.marketaux import FINANCIAL_SLUGS, MarketauxProvider
from app.providers.newsapi import NewsAPIProvider
from app.providers.rss import RSSProvider

logger = logging.getLogger(__name__)

_newsapi = NewsAPIProvider()
_gnews = GNewsProvider()
_marketaux = MarketauxProvider()
_rss = RSSProvider()


async def _safe_fetch(provider, *args, **kwargs) -> list[Article]:
    """Fetch from a provider and swallow errors so other providers continue."""
    try:
        return await provider.fetch(*args, **kwargs)
    except Exception as exc:
        logger.warning("Provider %s failed: %s", provider.name, exc)
        return []


async def fetch_for_interests(
    interest_slugs: list[str],
    query: str = "",
    language: str = "en",
    country: str = "",
    page_size_per_provider: int = 20,
) -> list[Article]:
    """
    Selects and calls appropriate providers based on the user's interests.
    Always tries NewsAPI + GNews for general interests.
    Marketaux is added for financial categories.
    RSS is used as a fallback / supplement.
    """
    slugs = interest_slugs or ["technology"]
    is_financial = any(s in FINANCIAL_SLUGS for s in slugs)

    # Build tasks
    tasks = [
        _safe_fetch(_newsapi, query, slugs, language, country, page_size_per_provider),
        _safe_fetch(_gnews, query, slugs, language, country, page_size_per_provider),
        _safe_fetch(_rss, query, slugs, language, country, page_size_per_provider),
    ]
    if is_financial:
        tasks.append(
            _safe_fetch(_marketaux, query, slugs, language, country, page_size_per_provider)
        )

    results_per_provider = await asyncio.gather(*tasks)
    all_articles: list[Article] = []
    for batch in results_per_provider:
        all_articles.extend(batch)

    return deduplicate(all_articles)


def deduplicate(articles: list[Article]) -> list[Article]:
    seen_urls: dict[str, Article] = {}
    seen_titles: set[str] = set()

    for article in articles:
        url_key = normalize_url(article.url)
        title_key = _title_key(article.title)

        if url_key in seen_urls:
            continue
        if title_key in seen_titles and len(title_key) > 20:
            continue

        seen_urls[url_key] = article
        seen_titles.add(title_key)

    return list(seen_urls.values())


def _title_key(title: str) -> str:
    """Normalized title for near-duplicate detection."""
    import re
    return re.sub(r"[^a-z0-9]", "", title.lower())[:80]
