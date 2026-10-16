from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any

from app.models import Article


def compute_score(
    article: Article,
    user_interests: list[str],
    positive_categories: set[str],
    negative_categories: set[str],
    liked_sources: set[str],
    disliked_sources: set[str],
    seen_ids: set[str],
    mode: str = "for_you",
) -> float:
    """
    Compute a ranking score for an article given user context.
    Higher = more relevant.
    """
    if mode == "latest":
        return _freshness_score(article)

    score = 0.0

    # Interest match
    article_cats = set(article.categories)
    interest_set = set(user_interests)
    overlap = len(article_cats & interest_set)
    if overlap:
        score += 20.0 * overlap

    # Freshness (decay over 48h)
    score += _freshness_score(article) * 10.0

    # Positive feedback from similar categories
    pos_overlap = len(article_cats & positive_categories)
    score += 5.0 * pos_overlap

    # Negative feedback penalty
    neg_overlap = len(article_cats & negative_categories)
    score -= 15.0 * neg_overlap

    # Publisher preference
    source = (article.source or "").lower()
    if source and source in liked_sources:
        score += 8.0
    if source and source in disliked_sources:
        score -= 10.0

    # Seen penalty — de-rank already-shown articles
    if article.id in seen_ids:
        score -= 30.0

    # Provider bonus (reward diversity)
    if article.provider == "newsapi":
        score += 1.0
    elif article.provider == "gnews":
        score += 0.5

    return score


def _freshness_score(article: Article) -> float:
    """Score from 0 to 1 based on how recent the article is (half-life = 12 h)."""
    if not article.published_at:
        return 0.3
    try:
        pub = datetime.fromisoformat(article.published_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        age_hours = max(0, (now - pub).total_seconds() / 3600)
        return math.exp(-age_hours / 12)
    except Exception:
        return 0.3


def rank_articles(
    articles: list[Article],
    user_interests: list[str],
    positive_categories: set[str],
    negative_categories: set[str],
    liked_sources: set[str],
    disliked_sources: set[str],
    seen_ids: set[str],
    mode: str = "for_you",
) -> list[Article]:
    scored = [
        (
            compute_score(
                a,
                user_interests,
                positive_categories,
                negative_categories,
                liked_sources,
                disliked_sources,
                seen_ids,
                mode,
            ),
            a,
        )
        for a in articles
    ]
    scored.sort(key=lambda x: x[0], reverse=True)

    # Ensure diversity: cap any single category at 40% of feed
    result: list[Article] = []
    category_counts: dict[str, int] = {}
    max_per_category = max(3, len(articles) // 3)

    for _, article in scored:
        cats = article.categories or ["general"]
        primary = cats[0] if cats else "general"
        count = category_counts.get(primary, 0)
        if count < max_per_category:
            result.append(article)
            category_counts[primary] = count + 1

    return result
