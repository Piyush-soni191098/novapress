from __future__ import annotations

from typing import Optional

# Complete category taxonomy. Each entry maps a slug to display info and
# associated search queries for providers that don't have native category support.

CATEGORIES: list[dict] = [
    # Technology
    {"slug": "technology", "name": "Technology", "icon": "💻", "description": "Products, software, and tech industry", "parent": None, "query": "technology software app"},
    {"slug": "artificial-intelligence", "name": "AI & Machine Learning", "icon": "🤖", "description": "Models, agents, research, LLMs", "parent": "technology", "query": '"artificial intelligence" OR "machine learning" OR LLM OR "AI agent"'},
    {"slug": "cybersecurity", "name": "Cybersecurity", "icon": "🔐", "description": "Security, hacking, data breaches", "parent": "technology", "query": "cybersecurity hacking data breach vulnerability"},
    {"slug": "open-source", "name": "Open Source", "icon": "⚙️", "description": "Open source projects and developer tools", "parent": "technology", "query": '"open source" developer tools GitHub'},

    # Business & Finance
    {"slug": "business", "name": "Business & Startups", "icon": "🏢", "description": "Startups, companies, entrepreneurship", "parent": None, "query": "business startup entrepreneur venture"},
    {"slug": "finance", "name": "Finance & Economics", "icon": "📊", "description": "Markets, economy, financial news", "parent": None, "query": "finance economics market investment"},
    {"slug": "stocks", "name": "Stocks & Investing", "icon": "📈", "description": "Stock market, trading, equities", "parent": "finance", "query": '"stock market" OR stocks OR shares OR IPO OR earnings'},
    {"slug": "cryptocurrency", "name": "Cryptocurrency", "icon": "₿", "description": "Bitcoin, Ethereum, DeFi, Web3", "parent": "finance", "query": "cryptocurrency bitcoin ethereum crypto blockchain"},
    {"slug": "personal-finance", "name": "Personal Finance", "icon": "💰", "description": "Budgeting, saving, personal investment", "parent": "finance", "query": '"personal finance" budgeting saving retirement'},
    {"slug": "real-estate", "name": "Real Estate", "icon": "🏠", "description": "Property, housing market, mortgage", "parent": "finance", "query": "real estate property housing market mortgage"},

    # Politics & World
    {"slug": "politics", "name": "Politics & Policy", "icon": "🏛️", "description": "Government, elections, public policy", "parent": None, "query": "politics government policy election parliament"},
    {"slug": "world-news", "name": "World News", "icon": "🌍", "description": "International news and geopolitics", "parent": None, "query": "world news international geopolitics diplomacy"},
    {"slug": "india-news", "name": "India & Regional", "icon": "🇮🇳", "description": "Indian news and South Asian coverage", "parent": "world-news", "query": "India news Delhi Mumbai government"},

    # Science & Health
    {"slug": "science", "name": "Science & Research", "icon": "🔬", "description": "Scientific discoveries and research", "parent": None, "query": "science research discovery study journal"},
    {"slug": "space", "name": "Space & Astronomy", "icon": "🚀", "description": "Space exploration, NASA, astronomy", "parent": "science", "query": "space astronomy NASA SpaceX planet telescope"},
    {"slug": "health", "name": "Health & Medicine", "icon": "🏥", "description": "Healthcare, medical research, wellness", "parent": None, "query": "health medicine medical healthcare wellness"},
    {"slug": "environment", "name": "Environment & Climate", "icon": "🌱", "description": "Climate change, sustainability, nature", "parent": "science", "query": "environment climate change sustainability ecology"},

    # Sports
    {"slug": "sports", "name": "Sports", "icon": "🏅", "description": "All sports news", "parent": None, "query": "sports athletics tournament championship"},
    {"slug": "cricket", "name": "Cricket", "icon": "🏏", "description": "Cricket matches, IPL, Test, ODI", "parent": "sports", "query": "cricket IPL test match ODI wicket"},
    {"slug": "football", "name": "Football / Soccer", "icon": "⚽", "description": "Premier League, Champions League, FIFA", "parent": "sports", "query": "football soccer Premier League FIFA Champions League"},
    {"slug": "basketball", "name": "Basketball", "icon": "🏀", "description": "NBA and international basketball", "parent": "sports", "query": "basketball NBA playoffs"},
    {"slug": "esports", "name": "Gaming & Esports", "icon": "🎮", "description": "Video games, esports tournaments", "parent": "sports", "query": "gaming esports video game tournament"},

    # Entertainment & Culture
    {"slug": "entertainment", "name": "Entertainment", "icon": "🎭", "description": "Celebrities, music, pop culture", "parent": None, "query": "entertainment celebrity music pop culture"},
    {"slug": "movies-tv", "name": "Movies & TV", "icon": "🎬", "description": "Films, streaming, television shows", "parent": "entertainment", "query": "movies film streaming television Netflix release"},

    # Lifestyle
    {"slug": "travel", "name": "Travel & Tourism", "icon": "✈️", "description": "Destinations, travel tips, tourism", "parent": None, "query": "travel tourism destination trip vacation"},
    {"slug": "food", "name": "Food & Cooking", "icon": "🍴", "description": "Recipes, restaurants, food culture", "parent": None, "query": "food cooking recipe restaurant cuisine"},
    {"slug": "lifestyle", "name": "Lifestyle & Fashion", "icon": "👗", "description": "Fashion, beauty, design, lifestyle", "parent": None, "query": "lifestyle fashion beauty design trend"},

    # Education & Careers
    {"slug": "education", "name": "Education & Careers", "icon": "🎓", "description": "Education, jobs, professional development", "parent": None, "query": "education career job university employment"},

    # Other
    {"slug": "automotive", "name": "Automotive & EVs", "icon": "🚗", "description": "Cars, electric vehicles, automotive industry", "parent": None, "query": "automotive electric vehicle EV car industry Tesla"},
    {"slug": "agriculture", "name": "Agriculture", "icon": "🌾", "description": "Farming, crops, agricultural policy", "parent": None, "query": "agriculture farming crop harvest agricultural policy"},
    {"slug": "legal", "name": "Legal & Regulatory", "icon": "⚖️", "description": "Laws, regulations, court decisions", "parent": None, "query": "legal regulatory court law regulation compliance"},
    {"slug": "history-culture", "name": "History & Culture", "icon": "🏛", "description": "History, culture, arts, heritage", "parent": None, "query": "history culture art heritage museum"},
]

_by_slug: dict[str, dict] = {c["slug"]: c for c in CATEGORIES}


def get_all_categories() -> list[dict]:
    return CATEGORIES


def get_category(slug: str) -> Optional[dict]:
    return _by_slug.get(slug)


def get_query_for_slugs(slugs: list[str]) -> str:
    """Build a combined search query for given category slugs."""
    queries = []
    for slug in slugs:
        cat = _by_slug.get(slug)
        if cat and cat.get("query"):
            queries.append(f"({cat['query']})")
    if not queries:
        return " OR ".join(slugs)
    # Join with OR, limit length
    combined = " OR ".join(queries)
    return combined[:300]


def search_categories(term: str) -> list[dict]:
    """Search categories by name or description."""
    term_lower = term.lower()
    return [
        c for c in CATEGORIES
        if term_lower in c["name"].lower()
        or term_lower in c["description"].lower()
        or term_lower in c["slug"].lower()
    ]
