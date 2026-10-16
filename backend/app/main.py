from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.routers import (
    bookmarks,
    categories,
    feed,
    health,
    insights,
    interactions,
    news,
    preferences,
    topics,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Personalized News Intelligence API",
    version="2.0.0",
    description="Multi-provider personalized news with Supabase Auth and adaptive recommendations.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Mount all routers
app.include_router(health.router)
app.include_router(categories.router)
app.include_router(news.router)
app.include_router(topics.router)
app.include_router(feed.router)
app.include_router(bookmarks.router)
app.include_router(interactions.router)
app.include_router(preferences.router)
app.include_router(insights.router)


@app.on_event("startup")
async def startup() -> None:
    logger.info("Starting Personalized News API v2.0")
    logger.info("NewsAPI: %s", "configured" if config.NEWSAPI_API_KEY else "NOT configured")
    logger.info("GNews: %s", "configured" if config.GNEWS_API_KEY else "NOT configured")
    logger.info("Marketaux: %s", "configured" if config.MARKETAUX_API_TOKEN else "NOT configured")
    logger.info("Supabase: %s", "configured" if config.supabase_configured() else "NOT configured — auth and persistence unavailable")
