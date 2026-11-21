"""Google Play Store review scraper for the Groww platform.

Fetches public reviews, filters to the 8–12 week window,
applies quality filters (>8 words, emojis stripped, English only),
sanitizes PII, and outputs raw and clean datasets.
"""

import json
import logging
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from google_play_scraper import reviews as fetch_reviews_batch, Sort
from src.config.settings import settings
from src.ingestion.models import RawReview, ReviewRecord
from src.ingestion.pii_sanitizer import PIISanitizer

logger = logging.getLogger(__name__)


class PlayStoreScraper:
    """Orchestrates public review ingestion from Google Play Store for Groww."""

    def __init__(
        self,
        app_id: Optional[str] = None,
        country: Optional[str] = None,
        lang: Optional[str] = None,
        sanitizer: Optional[PIISanitizer] = None,
    ) -> None:
        self.app_id = app_id or settings.app.package_id
        self.country = country or settings.app.country
        self.lang = lang or settings.app.lang
        self.sanitizer = sanitizer or PIISanitizer(strip_emojis=settings.ingestion.remove_emojis)

    def fetch_reviews(
        self,
        weeks_back: int = 10,
        max_sample: int = 1500,
        batch_size: int = 200,
        rate_limit_delay: float = 1.0,
    ) -> List[Dict[str, Any]]:
        """Paginate and fetch reviews for the target app within the given lookback window."""
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(weeks=weeks_back)

        logger.info(
            "Starting review ingestion for %s (weeks_back=%d, cutoff=%s)",
            self.app_id,
            weeks_back,
            cutoff_date.strftime("%Y-%m-%d"),
        )

        all_raw_reviews: List[Dict[str, Any]] = []
        seen_ids = set()
        continuation_token = None
        page = 1

        while len(all_raw_reviews) < max_sample:
            logger.info("Fetching batch %d (collected %d reviews so far)...", page, len(all_raw_reviews))
            try:
                batch, continuation_token = fetch_reviews_batch(
                    self.app_id,
                    lang=self.lang,
                    country=self.country,
                    sort=Sort.NEWEST,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
            except Exception as e:
                logger.error("Error during Play Store batch retrieval: %s", e)
                break

            if not batch:
                logger.info("No more reviews returned by Play Store.")
                break

            batch_added = 0
            reached_cutoff = False

            for item in batch:
                review_id = item.get("reviewId")
                if not review_id or review_id in seen_ids:
                    continue

                review_date = item.get("at")
                if isinstance(review_date, datetime):
                    if review_date.tzinfo is None:
                        review_date = review_date.replace(tzinfo=timezone.utc)

                    if review_date < cutoff_date:
                        reached_cutoff = True
                        break

                seen_ids.add(review_id)
                all_raw_reviews.append(item)
                batch_added += 1

                if len(all_raw_reviews) >= max_sample:
                    break

            logger.info("Batch %d: added %d valid reviews within timeframe.", page, batch_added)

            if reached_cutoff or not continuation_token or len(all_raw_reviews) >= max_sample:
                logger.info("Pagination completed. Reached cutoff: %s", reached_cutoff)
                break

            page += 1
            if rate_limit_delay > 0:
                time.sleep(rate_limit_delay)

        logger.info("Total raw reviews collected: %d", len(all_raw_reviews))
        return all_raw_reviews

    def process_and_sanitize(
        self,
        raw_reviews: List[Dict[str, Any]],
        min_word_count: Optional[int] = None,
        english_only: Optional[bool] = None,
    ) -> List[ReviewRecord]:
        """Validate, filter (>8 words, English only), strip emojis, and scrub PII."""
        min_words = min_word_count if min_word_count is not None else settings.ingestion.min_word_count
        filter_english = english_only if english_only is not None else settings.ingestion.english_only

        clean_records: List[ReviewRecord] = []
        total_redactions = 0
        filtered_short = 0
        filtered_non_english = 0

        for item in raw_reviews:
            try:
                raw_obj = RawReview.model_validate(item)
            except Exception as ex:
                logger.warning("Skipping malformed raw review item: %s", ex)
                continue

            # Sanitize review body (scrubs PII and strips emojis)
            clean_text, red_count = self.sanitizer.sanitize_text(raw_obj.content)
            total_redactions += red_count

            # Filter: Check word count (strictly > 8 words, i.e. >= min_words)
            words = clean_text.split()
            if len(words) < min_words:
                filtered_short += 1
                continue

            # Filter: English only (removes Hindi, regional scripts, Hinglish)
            if filter_english and not self.sanitizer.is_english(clean_text):
                filtered_non_english += 1
                continue

            # Anonymize user name
            anon_user = self.sanitizer.anonymize_user(raw_obj.userName or "")

            # Normalize review timestamp to naive datetime UTC
            date_val = raw_obj.at
            if date_val.tzinfo is not None:
                date_val = date_val.astimezone(timezone.utc).replace(tzinfo=None)

            record = ReviewRecord(
                review_id=raw_obj.reviewId,
                user_name_anonymized=anon_user,
                rating=raw_obj.score,
                title=None,
                text=clean_text,
                date=date_val,
                thumbs_up_count=raw_obj.thumbsUpCount,
                app_version=raw_obj.reviewCreatedVersion,
            )
            clean_records.append(record)

        logger.info(
            "Sanitization complete: %d clean English records kept (filtered %d short [<=8 words], %d non-English, %d PII redacted).",
            len(clean_records),
            filtered_short,
            filtered_non_english,
            total_redactions,
        )
        return clean_records

    def save_raw_reviews(
        self,
        raw_reviews: List[Dict[str, Any]],
        output_dir: Optional[Path | str] = None,
    ) -> Path:
        """Persist raw reviews to JSON for auditing and offline debugging."""
        out_dir = Path(output_dir or settings.storage.raw_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = out_dir / f"reviews_raw_{timestamp_str}.json"

        def json_serial(obj):
            if isinstance(obj, (datetime,)):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(raw_reviews, f, default=json_serial, indent=2, ensure_ascii=False)

        logger.info("Saved raw reviews to %s", file_path)
        return file_path

    def save_clean_reviews(
        self,
        clean_records: List[ReviewRecord],
        output_file: Optional[Path | str] = None,
    ) -> Path:
        """Persist sanitized reviews into clean JSONL format."""
        if output_file is None:
            out_path = Path(settings.storage.processed_dir) / "reviews_clean.jsonl"
        else:
            out_path = Path(output_file)

        out_path.parent.mkdir(parents=True, exist_ok=True)

        with open(out_path, "w", encoding="utf-8") as f:
            for rec in clean_records:
                f.write(rec.model_dump_json() + "\n")

        logger.info("Saved %d clean review records to %s", len(clean_records), out_path)
        return out_path


def run_ingestion(
    weeks_back: int = 10,
    max_sample: int = 1500,
    min_word_count: int = 9,
    english_only: bool = True
) -> Dict[str, Any]:
    """Convenience execution entrypoint for review ingestion."""
    scraper = PlayStoreScraper()
    raw = scraper.fetch_reviews(weeks_back=weeks_back, max_sample=max_sample)
    raw_path = scraper.save_raw_reviews(raw)
    clean = scraper.process_and_sanitize(raw, min_word_count=min_word_count, english_only=english_only)
    clean_path = scraper.save_clean_reviews(clean)

    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in clean:
        rating_counts[r.rating] += 1

    return {
        "raw_count": len(raw),
        "clean_count": len(clean),
        "raw_path": str(raw_path),
        "clean_path": str(clean_path),
        "rating_distribution": rating_counts,
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    result = run_ingestion()
    print("Ingestion Result:", json.dumps(result, indent=2))
