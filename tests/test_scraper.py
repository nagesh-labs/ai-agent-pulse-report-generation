"""Unit tests for PlayStoreScraper logic with mocked API responses."""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from src.ingestion.play_store_scraper import PlayStoreScraper


def test_scraper_date_cutoff_filtering(tmp_path):
    now = datetime.now(timezone.utc)
    recent_date = now - timedelta(days=7)      # 1 week ago (within 10 weeks)
    old_date = now - timedelta(days=100)       # ~14 weeks ago (beyond 10 weeks)

    mock_batch = [
        {
            "reviewId": "rev_recent",
            "userName": "Recent User",
            "content": "This is a sufficiently long recent review describing app behavior in detail.",
            "score": 4,
            "thumbsUpCount": 1,
            "reviewCreatedVersion": "2.14.0",
            "at": recent_date,
        },
        {
            "reviewId": "rev_old",
            "userName": "Old User",
            "content": "This is another long old review describing app behavior in detail.",
            "score": 1,
            "thumbsUpCount": 0,
            "reviewCreatedVersion": "2.10.0",
            "at": old_date,
        },
    ]

    with patch("src.ingestion.play_store_scraper.fetch_reviews_batch") as mock_fetch:
        mock_fetch.return_value = (mock_batch, None)

        scraper = PlayStoreScraper()
        reviews = scraper.fetch_reviews(weeks_back=10, rate_limit_delay=0)

        # Only the recent review should be returned
        assert len(reviews) == 1
        assert reviews[0]["reviewId"] == "rev_recent"


def test_process_quality_filters_and_pii(tmp_path):
    """Verify that reviews <=8 words, non-English reviews, and PII are properly handled."""
    mock_batch = [
        # Short review (4 words) -> MUST BE FILTERED OUT
        {
            "reviewId": "rev_short",
            "userName": "Short User",
            "content": "Very good app 👍",
            "score": 5,
            "thumbsUpCount": 0,
            "reviewCreatedVersion": "2.14.0",
            "at": datetime.now(),
        },
        # Non-English / Hindi review -> MUST BE FILTERED OUT
        {
            "reviewId": "rev_hindi",
            "userName": "Hindi User",
            "content": "भाई पी डालने के बाद वेरीफाई के टाइम पर ओटीपी नहीं आ रहा है क्या करूँ",
            "score": 1,
            "thumbsUpCount": 0,
            "reviewCreatedVersion": "2.14.0",
            "at": datetime.now(),
        },
        # Valid English review (>8 words, with emojis and PII) -> MUST BE KEPT AND SANITIZED
        {
            "reviewId": "rev_valid",
            "userName": "Ramesh Phone 9876543210",
            "content": "I am unable to access my funds. Call me on 9876543210 or email test@groww.in please fix urgently! 😡",
            "score": 1,
            "thumbsUpCount": 3,
            "reviewCreatedVersion": "2.14.0",
            "at": datetime.now(),
        }
    ]

    scraper = PlayStoreScraper()
    clean_records = scraper.process_and_sanitize(mock_batch, min_word_count=9, english_only=True)

    # Only rev_valid should be kept!
    assert len(clean_records) == 1
    record = clean_records[0]
    assert record.review_id == "rev_valid"
    assert record.user_name_anonymized == "Reviewer #0001"
    assert "[REDACTED_PHONE]" in record.text
    assert "[REDACTED_EMAIL]" in record.text
    assert "9876543210" not in record.text
    assert "test@groww.in" not in record.text
    assert "😡" not in record.text  # Emoji stripped!
    assert len(record.text.split()) > 8  # More than 8 words!

    # Save to temp file
    out_file = tmp_path / "reviews_clean.jsonl"
    saved_path = scraper.save_clean_reviews(clean_records, output_file=out_file)
    assert saved_path.exists()
    assert saved_path.stat().st_size > 0
