"""Unit tests for ThematicClusterer and severity ranking."""

from datetime import datetime
import pytest
from src.ingestion.models import ReviewRecord
from src.agent.clusterer import ThematicClusterer, DOMAIN_TAXONOMY


@pytest.fixture
def sample_reviews():
    return [
        ReviewRecord(
            review_id="r1",
            user_name_anonymized="Reviewer #0001",
            rating=1,
            text="Stop loss not triggered during market fall and lost 30000 rupees.",
            date=datetime.now(),
            thumbs_up_count=10,
        ),
        ReviewRecord(
            review_id="r2",
            user_name_anonymized="Reviewer #0002",
            rating=1,
            text="Adapter disconnected error while placing exit order for F&O position.",
            date=datetime.now(),
            thumbs_up_count=5,
        ),
        ReviewRecord(
            review_id="r3",
            user_name_anonymized="Reviewer #0003",
            rating=1,
            text="CAMS statement mismatch and mutual funds display wrong XIRR.",
            date=datetime.now(),
            thumbs_up_count=2,
        ),
        ReviewRecord(
            review_id="r4",
            user_name_anonymized="Reviewer #0004",
            rating=2,
            text="Charts are not opening and showing failed to load in network.",
            date=datetime.now(),
            thumbs_up_count=1,
        ),
        ReviewRecord(
            review_id="r5",
            user_name_anonymized="Reviewer #0005",
            rating=5,
            text="Very good and user friendly app for stock market investing.",
            date=datetime.now(),
            thumbs_up_count=0,
        ),
    ]


def test_cluster_reviews_bound(sample_reviews):
    clusterer = ThematicClusterer()
    themes = clusterer.cluster_reviews(sample_reviews)

    # Clustered themes must never exceed 5
    assert len(themes) <= 5
    assert len(themes) == len(DOMAIN_TAXONOMY)


def test_severity_ranking_prioritizes_trading_friction(sample_reviews):
    clusterer = ThematicClusterer()
    themes = clusterer.cluster_reviews(sample_reviews)

    # Trading theme has two 1-star reviews and 15 thumbs up -> highest priority
    top_theme = themes[0]
    assert "Trading & Order Execution" in top_theme.name
    assert top_theme.priority_score > themes[-1].priority_score


def test_get_top_themes_and_quotes(sample_reviews):
    clusterer = ThematicClusterer()
    top_themes, quotes = clusterer.get_top_themes_and_quotes(sample_reviews, top_n=3)

    assert len(top_themes) == 3
    assert len(quotes) == 3

    for q in quotes:
        assert q.is_verified is True
        assert len(q.quote_text.split()) >= 5

