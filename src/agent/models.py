"""Data schemas and Pydantic models for Phase 2 Agentic Analysis and Pulse Synthesis."""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ClusteredTheme(BaseModel):
    """Represents an identified domain theme aggregated from reviews."""
    model_config = ConfigDict(frozen=True)

    theme_id: str
    name: str = Field(description="Domain theme title")
    description: str = Field(description="Summary of core friction points in this theme")
    review_count: int = Field(ge=0, description="Total reviews mapped to this theme")
    rating_breakdown: Dict[int, int] = Field(default_factory=dict, description="Distribution of 1-5 star ratings")
    thumbs_up_sum: int = Field(default=0, description="Cumulative thumbs up / helpful votes")
    priority_score: float = Field(default=0.0, description="Calculated composite severity score")
    sample_review_ids: List[str] = Field(default_factory=list, description="IDs of representative reviews")


class VerbatimQuote(BaseModel):
    """An exact, unaltered user quote extracted from a verified review."""
    model_config = ConfigDict(frozen=True)

    review_id: str
    user_pseudonym: str
    rating: int
    quote_text: str = Field(description="Exact substring from raw review text")
    theme_name: str
    is_verified: bool = Field(default=False, description="Deterministic substring check status")


class ActionItem(BaseModel):
    """Concrete engineering or product recommendation grounded in user feedback."""
    model_config = ConfigDict(frozen=True)

    item_id: int = Field(ge=1, le=3)
    title: str = Field(description="Action title")
    recommendation: str = Field(description="Concrete next step with engineering/product specificity")
    target_theme: str = Field(description="Associated theme name")


class ExecutivePulsePayload(BaseModel):
    """Final weekly executive pulse note payload adhering to all project constraints."""
    model_config = ConfigDict(frozen=True)

    date_range: str = Field(description="Lookback timeframe (e.g. Aug 23, 2026 - Nov 01, 2026)")
    total_reviews_analyzed: int = Field(ge=1)
    top_themes: List[ClusteredTheme] = Field(min_length=3, max_length=3)
    verbatim_quotes: List[VerbatimQuote] = Field(min_length=3, max_length=3)
    action_ideas: List[ActionItem] = Field(min_length=3, max_length=3)
    pulse_markdown: str = Field(description="The complete scannable executive note in markdown")
    word_count: int = Field(le=250, description="Strict total word count limit (<= 250 words)")

