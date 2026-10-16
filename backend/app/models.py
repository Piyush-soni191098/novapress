from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class Article(BaseModel):
    id: str
    title: str
    description: str = ""
    url: str
    image_url: Optional[str] = None
    source: str = ""
    author: Optional[str] = None
    published_at: str = ""
    categories: list[str] = Field(default_factory=list)
    language: str = "en"
    country: Optional[str] = None
    provider: str = ""
    financial_entities: list[str] = Field(default_factory=list)
    relevance_score: float = 0.0
    retrieved_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )

    @field_validator("url", mode="before")
    @classmethod
    def clean_url(cls, v: Any) -> str:
        return str(v or "").strip()

    @field_validator("title", mode="before")
    @classmethod
    def clean_title(cls, v: Any) -> str:
        return str(v or "").strip()


class UserPreferences(BaseModel):
    language: str = "en"
    country: Optional[str] = None
    muted_topics: list[str] = Field(default_factory=list)
    preferred_publishers: list[str] = Field(default_factory=list)
    tracking_enabled: bool = True


class UserInterest(BaseModel):
    category_slug: str
    strength: float = 1.0


class InteractionEvent(BaseModel):
    article_id: str
    article_url: str
    event_type: str
    topic_slug: Optional[str] = None
    provider: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        allowed = {
            "impression", "click", "bookmark", "unbookmark",
            "like", "dislike", "hide", "more_like_this", "less_like_this",
            "follow_topic", "unfollow_topic", "mute_topic", "share",
            "search_result_click",
        }
        if v not in allowed:
            raise ValueError(f"Unknown event_type: {v}")
        return v


class BatchInteractionRequest(BaseModel):
    events: list[InteractionEvent]


class BookmarkCreate(BaseModel):
    article_id: str
    article_url: str
    title: str
    description: str = ""
    image_url: Optional[str] = None
    source: str = ""
    published_at: str = ""
    provider: str = ""
    categories: list[str] = Field(default_factory=list)


class PreferencesUpdate(BaseModel):
    language: Optional[str] = None
    country: Optional[str] = None
    muted_topics: Optional[list[str]] = None
    preferred_publishers: Optional[list[str]] = None
    tracking_enabled: Optional[bool] = None


class OnboardingData(BaseModel):
    display_name: Optional[str] = None
    interests: list[str] = Field(default_factory=list)
    language: str = "en"
    country: Optional[str] = None
    muted_topics: list[str] = Field(default_factory=list)
    preferred_publishers: list[str] = Field(default_factory=list)
    tracking_enabled: bool = True


class FeedRequest(BaseModel):
    page: int = Field(default=1, ge=1, le=100)
    page_size: int = Field(default=20, ge=1, le=60)
    mode: str = Field(default="for_you")  # for_you | latest | following
    language: str = "en"
    location: str = ""
