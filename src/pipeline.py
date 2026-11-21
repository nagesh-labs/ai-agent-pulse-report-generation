"""End-to-End Orchestration Pipeline for Groww Mobile App Feedback Pulse.

Integrates:
1. Review ingestion & PII hygiene (Phase 1)
2. Hybrid domain semantic clustering, verbatim quotes, actions, & distillation (Phase 2)
3. Delivery to Google Docs and Gmail via Vercel MCP Server (Phase 3)
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import timedelta

from dotenv import load_dotenv

# Ensure UTF-8 output encoding on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

from src.config.settings import settings
from src.ingestion.models import ReviewRecord
from src.ingestion.play_store_scraper import PlayStoreScraper
from src.agent.llm_client import AgentSynthesisCoordinator
from src.mcp.client import VercelMCPClient, MCPClientError
from src.mcp.docs_tool import GoogleDocsTool
from src.mcp.gmail_tool import GmailTool

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("groww_pulse_pipeline")


class GrowwPulsePipeline:
    """Orchestrates the entire feedback pulse pipeline from ingestion to delivery."""

    def __init__(
        self,
        mcp_client: Optional[VercelMCPClient] = None,
        coordinator: Optional[AgentSynthesisCoordinator] = None,
    ) -> None:
        self.mcp_client = mcp_client or VercelMCPClient()
        self.coordinator = coordinator or AgentSynthesisCoordinator()
        self.docs_tool = GoogleDocsTool(mcp_client=self.mcp_client)
        self.gmail_tool = GmailTool(mcp_client=self.mcp_client)

    def load_or_fetch_reviews(
        self,
        clean_path: Optional[Path] = None,
        scrape_fresh: bool = False,
        weeks_back: int = 10,
    ) -> list[ReviewRecord]:
        """Loads clean reviews from disk or fetches fresh reviews from the Google Play Store."""
        path = clean_path or Path("data/processed/reviews_clean.jsonl")

        if scrape_fresh or not path.exists():
            logger.info("Fetching fresh reviews from Google Play Store...")
            scraper = PlayStoreScraper()
            raw_reviews = scraper.fetch_reviews(weeks_back=weeks_back)
            records = scraper.process_and_save(raw_reviews)
            return records

        logger.info("Loading sanitized reviews from cached dataset: %s", path)
        reviews = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    reviews.append(ReviewRecord.model_validate_json(line))

        if reviews and weeks_back:
            latest_date = max(r.date for r in reviews)
            cutoff_date = latest_date - timedelta(weeks=weeks_back)
            filtered = [r for r in reviews if r.date >= cutoff_date]
            if filtered:
                logger.info(
                    "Filtered cached reviews for past %d weeks: %d of %d reviews retained (>= %s)",
                    weeks_back, len(filtered), len(reviews), cutoff_date.strftime("%Y-%m-%d")
                )
                return filtered

        return reviews

    def run(
        self,
        scrape_fresh: bool = False,
        weeks_back: int = 10,
        dry_run: bool = False,
        doc_id: Optional[str] = None,
        recipient_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute the end-to-end pulse generation and delivery pipeline.

        Returns:
            Dict[str, Any]: Complete execution summary including payload and delivery results.
        """
        logger.info("Starting Groww Mobile App Feedback Pulse Pipeline...")

        # 1. Ingestion / Data Loading
        reviews = self.load_or_fetch_reviews(scrape_fresh=scrape_fresh, weeks_back=weeks_back)
        if not reviews:
            raise ValueError("No eligible reviews available to process.")

        # 2. Synthesis (Clustering -> Quote Verification -> Actions -> Distillation)
        pulse_payload = self.coordinator.generate_weekly_pulse(reviews)

        # 3. Delivery via MCP: Google Docs
        target_doc = doc_id or os.getenv("GOOGLE_DOC_ID") or settings.delivery.google_doc_id
        docs_res: Dict[str, Any] = {}
        try:
            docs_res = self.docs_tool.append_pulse(
                content=pulse_payload.pulse_markdown,
                document_id=target_doc,
                dry_run=dry_run,
            )
        except Exception as e:
            logger.error("Failed to append pulse to Google Doc: %s", e)
            docs_res = {
                "status": "error",
                "summary": str(e),
                "document_url": f"https://docs.google.com/document/d/{target_doc}/edit",
            }

        # 4. Delivery via MCP: Gmail
        target_email = recipient_email or os.getenv("PULSE_EMAIL_RECIPIENT") or settings.delivery.email_recipient
        gmail_res: Dict[str, Any] = {}
        try:
            doc_link = docs_res.get("document_url", f"https://docs.google.com/document/d/{target_doc}/edit")
            gmail_res = self.gmail_tool.send_pulse_email(
                content=pulse_payload.pulse_markdown,
                recipient=target_email,
                google_doc_url=doc_link,
                date_range=pulse_payload.date_range,
                dry_run=dry_run,
            )
        except Exception as e:
            logger.error("Failed to send pulse email via Gmail: %s", e)
            gmail_res = {
                "status": "error",
                "summary": str(e),
                "recipient": target_email,
            }

        return {
            "status": "completed",
            "reviews_analyzed": len(reviews),
            "date_range": pulse_payload.date_range,
            "word_count": pulse_payload.word_count,
            "themes_count": len(pulse_payload.top_themes),
            "quotes_count": len(pulse_payload.verbatim_quotes),
            "actions_count": len(pulse_payload.action_ideas),
            "top_themes": [t.model_dump() for t in pulse_payload.top_themes],
            "verbatim_quotes": [q.model_dump() for q in pulse_payload.verbatim_quotes],
            "action_ideas": [a.model_dump() for a in pulse_payload.action_ideas],
            "pulse_markdown": pulse_payload.pulse_markdown,
            "google_doc_result": docs_res,
            "gmail_result": gmail_res,
        }


def main():
    parser = argparse.ArgumentParser(description="Groww Mobile App Feedback Pulse Automation Pipeline")
    parser.add_argument("--scrape", action="store_true", help="Scrape fresh reviews from Google Play Store")
    parser.add_argument("--weeks", type=int, default=10, help="Lookback window in weeks (default: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Run without mutating Google Docs or sending real emails")
    parser.add_argument("--doc-id", type=str, default=None, help="Custom Google Doc ID")
    parser.add_argument("--email-to", type=str, default=None, help="Custom recipient email address")

    args = parser.parse_args()

    pipeline = GrowwPulsePipeline()
    result = pipeline.run(
        scrape_fresh=args.scrape,
        weeks_back=args.weeks,
        dry_run=args.dry_run,
        doc_id=args.doc_id,
        recipient_email=args.email_to,
    )

    print("\n" + "=" * 80)
    print("GROWW APP FEEDBACK PULSE - EXECUTION REPORT")
    print("=" * 80)
    print(f"Reviews Analyzed : {result['reviews_analyzed']}")
    print(f"Date Range       : {result['date_range']}")
    print(f"Word Count       : {result['word_count']} words (Constraint: <= 250 words)")
    print(f"Themes Count     : {result['themes_count']} (Constraint: exactly 3)")
    print(f"Quotes Count     : {result['quotes_count']} (Constraint: exactly 3)")
    print(f"Actions Count    : {result['actions_count']} (Constraint: exactly 3)")
    print("\n" + "-" * 60)
    print("SYNTHESIZED PULSE NOTE:")
    print("-" * 60)
    print(result["pulse_markdown"])
    print("-" * 60)
    print("\nDELIVERY STATUS:")
    print(f"Google Docs : {result['google_doc_result'].get('status')}")
    print(f"  Summary   : {result['google_doc_result'].get('summary')}")
    print(f"  URL       : {result['google_doc_result'].get('document_url')}")
    print(f"Gmail       : {result['gmail_result'].get('status')}")
    print(f"  Summary   : {result['gmail_result'].get('summary')}")
    print(f"  Recipient : {result['gmail_result'].get('recipient')}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
