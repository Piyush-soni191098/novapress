from __future__ import annotations

import logging
from typing import Any, Optional

from app import config
from app.models import Article
from app.providers.selector import fetch_for_interests
from app.services.categories import get_query_for_slugs
from app.services.ranking import rank_articles

logger = logging.getLogger(__name__)


async def get_personalized_feed(
    interest_slugs: list[str],
    mode: str = "for_you",
    language: str = "en",
    country: str = "",
    page: int = 1,
    page_size: int = 20,
    seen_ids: Optional[set[str]] = None,
    positive_categories: Optional[set[str]] = None,
    negative_categories: Optional[set[str]] = None,
    liked_sources: Optional[set[str]] = None,
    disliked_sources: Optional[set[str]] = None,
    extra_query: str = "",
) -> dict[str, Any]:
    """
    Fetch, rank, and return a page of articles for the given user context.
    Falls back to general technology news for new users with no interests.
    """
    slugs = interest_slugs or ["technology", "world-news"]

    # Build a search query from the user's interests
    query = get_query_for_slugs(slugs[:5]) if not extra_query else extra_query

    articles = await fetch_for_interests(
        interest_slugs=slugs,
        query=query,
        language=language,
        country=country,
        page_size_per_provider=config.MAX_ARTICLES_PER_PROVIDER,
    )

    if not articles:
        return {
            "articles": [],
            "page": page,
            "page_size": page_size,
            "total_fetched": 0,
            "mode": mode,
        }

    ranked = rank_articles(
        articles=articles,
        user_interests=slugs,
        positive_categories=positive_categories or set(),
        negative_categories=negative_categories or set(),
        liked_sources=liked_sources or set(),
        disliked_sources=disliked_sources or set(),
        seen_ids=seen_ids or set(),
        mode=mode,
    )

    start = (page - 1) * page_size
    end = start + page_size
    page_articles = ranked[start:end]

    return {
        "articles": [a.model_dump() for a in page_articles],
        "page": page,
        "page_size": page_size,
        "total_fetched": len(ranked),
        "mode": mode,
    }


async def get_topic_feed(
    topic_slug: str,
    language: str = "en",
    country: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Fetch articles for a single topic."""
    from app.services.categories import get_query_for_slugs, get_category
    cat = get_category(topic_slug)
    query = cat["query"] if cat else topic_slug
    articles = await fetch_for_interests(
        interest_slugs=[topic_slug],
        query=query,
        language=language,
        country=country,
        page_size_per_provider=config.MAX_ARTICLES_PER_PROVIDER,
    )
    ranked = rank_articles(
        articles=articles,
        user_interests=[topic_slug],
        positive_categories=set(),
        negative_categories=set(),
        liked_sources=set(),
        disliked_sources=set(),
        seen_ids=set(),
        mode="for_you",
    )
    start = (page - 1) * page_size
    return {
        "articles": [a.model_dump() for a in ranked[start: start + page_size]],
        "page": page,
        "page_size": page_size,
        "total_fetched": len(ranked),
        "topic": topic_slug,
    }
