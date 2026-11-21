"""Unit tests for Review data models."""

from datetime import datetime
import pytest
from pydantic import ValidationError
from src.ingestion.models import RawReview, ReviewRecord


def test_raw_review_valid():
    raw_data = {
        "reviewId": "gp:AOqpTOE...",
        "userName": "Rohan Gupta",
        "content": "Good app for mutual funds",
        "score": 5,
        "thumbsUpCount": 12,
        "reviewCreatedVersion": "2.14.0",
        "at": datetime(2026, 10, 15, 10, 30, 0),
    }
    obj = RawReview.model_validate(raw_data)
    assert obj.reviewId == "gp:AOqpTOE..."
    assert obj.score == 5
    assert obj.thumbsUpCount == 12


def test_raw_review_invalid_score():
    raw_data = {
        "reviewId": "gp:123",
        "content": "Invalid rating",
        "score": 6,  # Ratings must be 1 to 5
        "at": datetime.now(),
    }
    with pytest.raises(ValidationError):
        RawReview.model_validate(raw_data)


def test_review_record_serialization():
    record = ReviewRecord(
        review_id="rev_1001",
        user_name_anonymized="Reviewer #0042",
        rating=2,
        title=None,
        text="Withdrawal takes 3 days, please speed up.",
        date=datetime(2026, 10, 20, 14, 0, 0),
        thumbs_up_count=5,
        app_version="2.14.1",
    )
    json_str = record.model_dump_json()
    assert "Reviewer #0042" in json_str
    assert "Withdrawal takes 3 days" in json_str

    deserialized = ReviewRecord.model_validate_json(json_str)
    assert deserialized == record

