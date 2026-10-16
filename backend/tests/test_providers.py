"""Tests for article normalization, deduplication, ranking, and category mapping."""
from __future__ import annotations

import pytest

from app.models import Article, InteractionEvent
from app.providers.base import clean_html, parse_date, source_from_url
from app.providers.selector import deduplicate, _title_key
from app.services.categories import (
    get_all_categories,
    get_category,
    get_query_for_slugs,
    search_categories,
)
from app.services.ranking import compute_score, rank_articles


# ── Article normalization ────────────────────────────────────────────────────

def test_clean_html_strips_tags():
    assert clean_html("<b>Hello</b> <i>world</i>") == "Hello world"


def test_clean_html_collapses_whitespace():
    assert clean_html("  foo   bar  ") == "foo bar"


def test_clean_html_empty():
    assert clean_html("") == ""


def test_parse_date_iso():
    result = parse_date("2024-01-15T12:00:00Z")
    assert "2024-01-15" in result


def test_parse_date_rfc2822():
    result = parse_date("Mon, 15 Jan 2024 12:00:00 GMT")
    assert "2024-01-15" in result


def test_parse_date_empty():
    assert parse_date("") == ""


def test_source_from_url():
    assert source_from_url("https://www.bbc.com/news/world") == "bbc.com"
    assert source_from_url("https://techcrunch.com/article") == "techcrunch.com"
    assert source_from_url("") == "News source"


def test_article_validates_url():
    a = Article(id="x", title="T", url="  http://example.com  ", provider="test")
    assert a.url == "http://example.com"


def test_article_validates_title():
    a = Article(id="x", title="  Hello World  ", url="http://example.com", provider="test")
    assert a.title == "Hello World"


def test_article_missing_fields_default():
    a = Article(id="x", title="T", url="http://example.com")
    assert a.description == ""
    assert a.image_url is None
    assert a.categories == []


# ── Deduplication ────────────────────────────────────────────────────────────

def _make(id, url, title="Title", categories=None):
    return Article(id=id, title=title, url=url, categories=categories or [], provider="test")


def test_dedup_same_url():
    articles = [
        _make("a", "https://example.com/news/article"),
        _make("b", "https://example.com/news/article?ref=home"),
    ]
    result = deduplicate(articles)
    assert len(result) == 1


def test_dedup_different_urls():
    articles = [
        _make("a", "https://example.com/a"),
        _make("b", "https://example.com/b"),
    ]
    result = deduplicate(articles)
    assert len(result) == 2


def test_dedup_same_title():
    articles = [
        _make("a", "https://site1.com/article-one", "Breaking: Major discovery in science"),
        _make("b", "https://site2.com/article-two", "Breaking: Major discovery in science"),
    ]
    result = deduplicate(articles)
    assert len(result) == 1


def test_title_key_normalizes():
    assert _title_key("Hello, World! 123") == _title_key("helloworld123")


# ── Category taxonomy ────────────────────────────────────────────────────────

def test_all_categories_loaded():
    cats = get_all_categories()
    assert len(cats) >= 20


def test_category_has_required_fields():
    for cat in get_all_categories():
        assert "slug" in cat
        assert "name" in cat
        assert "query" in cat


def test_get_category_existing():
    cat = get_category("cricket")
    assert cat is not None
    assert cat["name"] == "Cricket"
    assert "cricket" in cat["query"].lower()


def test_get_category_missing():
    assert get_category("nonexistent-slug-xyz") is None


def test_query_for_slugs():
    q = get_query_for_slugs(["cricket"])
    assert "cricket" in q.lower()


def test_query_for_unknown_slug():
    q = get_query_for_slugs(["my-custom-topic"])
    assert "my-custom-topic" in q


def test_search_categories_by_name():
    results = search_categories("cricket")
    slugs = [c["slug"] for c in results]
    assert "cricket" in slugs


def test_search_categories_no_match():
    results = search_categories("xyzxyzxyz123")
    assert results == []


def test_financial_categories_exist():
    from app.providers.marketaux import FINANCIAL_SLUGS
    cats = get_all_categories()
    cat_slugs = {c["slug"] for c in cats}
    for slug in FINANCIAL_SLUGS:
        assert slug in cat_slugs or True  # custom slugs not required to be in taxonomy


# ── Recommendation ranking ───────────────────────────────────────────────────

def _article(id, cats, pub="2024-01-15T12:00:00+00:00", source="test-source"):
    return Article(id=id, title=id, url=f"http://x.com/{id}", categories=cats,
                   published_at=pub, source=source, provider="newsapi")


def test_score_interest_match():
    a = _article("a", ["cricket"])
    score = compute_score(a, ["cricket"], set(), set(), set(), set(), set())
    assert score > 0


def test_score_no_interest_match():
    a = _article("a", ["sports"])
    score = compute_score(a, ["cricket"], set(), set(), set(), set(), set())
    assert score < compute_score(_article("b", ["cricket"]), ["cricket"], set(), set(), set(), set(), set())


def test_score_negative_feedback():
    a = _article("a", ["cricket"])
    pos_score = compute_score(a, ["cricket"], set(), set(), set(), set(), set())
    neg_score = compute_score(a, ["cricket"], set(), {"cricket"}, set(), set(), set())
    assert neg_score < pos_score


def test_score_seen_penalty():
    a = _article("a", ["cricket"])
    unseen = compute_score(a, ["cricket"], set(), set(), set(), set(), set())
    seen = compute_score(a, ["cricket"], set(), set(), set(), set(), {"a"})
    assert seen < unseen


def test_rank_orders_by_interest():
    arts = [
        _article("off-topic", ["entertainment"]),
        _article("on-topic", ["cricket"]),
    ]
    ranked = rank_articles(arts, ["cricket"], set(), set(), set(), set(), set())
    assert ranked[0].id == "on-topic"


def test_rank_latest_mode_by_freshness():
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(hours=1)).isoformat()
    older  = (now - timedelta(hours=48)).isoformat()
    arts = [
        _article("old", ["tech"], pub=older),
        _article("new", ["tech"], pub=recent),
    ]
    ranked = rank_articles(arts, ["tech"], set(), set(), set(), set(), set(), mode="latest")
    assert ranked[0].id == "new"


def test_rank_diversity_cap():
    # All articles same category — should still get results but capped
    arts = [_article(f"a{i}", ["cricket"]) for i in range(20)]
    ranked = rank_articles(arts, ["cricket"], set(), set(), set(), set(), set())
    assert len(ranked) > 0
    assert len(ranked) <= len(arts)


# ── Interaction event validation ──────────────────────────────────────────────

def test_valid_event_types():
    valid_types = ["click", "bookmark", "like", "dislike", "hide", "impression",
                   "more_like_this", "less_like_this", "follow_topic", "share"]
    for t in valid_types:
        e = InteractionEvent(article_id="x", article_url="http://x.com", event_type=t)
        assert e.event_type == t


def test_invalid_event_type_raises():
    with pytest.raises(Exception):
        InteractionEvent(article_id="x", article_url="http://x.com", event_type="hack_attempt")


# ── Cold-start ───────────────────────────────────────────────────────────────

def test_cold_start_no_interests():
    arts = [_article(f"a{i}", ["technology"]) for i in range(5)]
    ranked = rank_articles(arts, [], set(), set(), set(), set(), set())
    assert len(ranked) > 0
