"""Data schemas and Pydantic models for raw and processed store reviews."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RawReview(BaseModel):
    """Raw review payload directly retrieved from Google Play Store."""
    model_config = ConfigDict(extra="ignore")

    reviewId: str
    userName: Optional[str] = "Anonymous"
    userImage: Optional[str] = None
    content: str = ""
    score: int = Field(ge=1, le=5)
    thumbsUpCount: int = 0
    reviewCreatedVersion: Optional[str] = None
    at: datetime
    replyContent: Optional[str] = None
    repliedAt: Optional[datetime] = None


class ReviewRecord(BaseModel):
    """Sanitized, PII-scrubbed, normalized review record used throughout the AI pipeline."""
    model_config = ConfigDict(frozen=True)

    review_id: str = Field(description="Unique identifier from store")
    user_name_anonymized: str = Field(description="Anonymized user identifier (e.g., Reviewer #0142)")
    rating: int = Field(ge=1, le=5, description="1 to 5 star rating")
    title: Optional[str] = Field(default=None, description="Review title if provided")
    text: str = Field(description="Sanitized review body with all PII scrubbed")
    date: datetime = Field(description="Submission timestamp")
    thumbs_up_count: int = Field(default=0, description="Helpful/thumbs up count")
    app_version: Optional[str] = Field(default=None, description="App version when reviewed")

