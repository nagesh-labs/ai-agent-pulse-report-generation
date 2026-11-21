"""Thematic Clustering Engine using Hybrid Domain-Anchored Semantic Analysis.

Classifies Groww mobile app reviews into at most 5 operational domains,
calculates composite severity-weighted priority scores, and selects the Top 3 themes.
"""

import logging
from typing import List, Dict, Tuple
from src.ingestion.models import ReviewRecord
from src.agent.models import ClusteredTheme, VerbatimQuote
from src.agent.quote_verifier import QuoteVerifier

logger = logging.getLogger(__name__)


# Pre-defined Groww operational domain taxonomy anchors
DOMAIN_TAXONOMY = {
    "trading_execution": {
        "name": "Trading & Order Execution (F&O / Intraday)",
        "description": "Critical execution failures including stop-loss misses, exit freezes, and websocket adapter disconnects.",
        "keywords": [
            "stop loss", "stoploss", "exit", "adapter", "f&o", "trade", "trading",
            "scalper", "scalping", "position", "order", "option", "options", "intraday",
            "sensex", "nifty", "bse", "loss", "strike", "call", "put", "trigger",
            "execution", "manipulate", "dispute"
        ],
    },
    "portfolio_mf": {
        "name": "Portfolio Tracking & Mutual Funds Sync",
        "description": "Portfolio synchronization issues, CAMS statement reconciliation mismatches, and SIP tracking/redemption delays.",
        "keywords": [
            "mutual fund", "mutual funds", "sip", "cams", "xirr", "portfolio",
            "allocation", "redeem", "redemption", "statement", "statements",
            "nav", "units", "locking", "holding", "holdings"
        ],
    },
    "chart_stability": {
        "name": "Chart Performance & App UI Stability",
        "description": "Platform stability issues such as chart loading failures, candlestick de-sync, and lack of Android/tablet feature parity.",
        "keywords": [
            "chart", "charts", "failed to load", "freeze", "freezes", "hang", "hanging",
            "lag", "laggy", "candle", "landscape", "tablet", "preview", "crash",
            "crashes", "slow", "network", "screen"
        ],
    },
    "charges_support": {
        "name": "Brokerage, Charges & Transparency",
        "description": "Disputes regarding high F&O brokerage, unexpected account update charges, and generic customer support responses.",
        "keywords": [
            "brokerage", "charge", "charges", "fee", "fees", "gst", "hidden",
            "customer support", "customer care", "customer service", "ticket",
            "complaint", "support team", "reinstall", "expensive", "farji"
        ],
    },
    "onboarding_ipo": {
        "name": "Account Onboarding, IPO & Banking",
        "description": "Friction during IPO allotment, UPI ID modifications, bank account linking (SBI US wallet), and KYC permission objections.",
        "keywords": [
            "ipo", "allot", "allotting", "allotment", "bank", "sbi", "wallet",
            "kyc", "pan", "permission", "aadhaar", "otp", "account opening",
            "unblock", "cameroun", "deposit", "withdraw"
        ],
    },
}


class ThematicClusterer:
    """Clusters reviews into domain anchors and prioritizes the Top 3 themes."""

    def __init__(self, taxonomy: Dict[str, Dict] = None) -> None:
        self.taxonomy = taxonomy or DOMAIN_TAXONOMY

    def classify_review(self, text: str) -> str:
        """Classify a single review text into the best-matching domain anchor ID."""
        text_lower = text.lower()
        scores = {}

        for theme_id, meta in self.taxonomy.items():
            score = 0
            for kw in meta["keywords"]:
                if kw in text_lower:
                    # Multi-word phrase matches carry higher semantic weight
                    weight = 2.5 if " " in kw else 1.0
                    score += weight
            scores[theme_id] = score

        # If review has no specific keyword matches, check general sentiment indicators
        best_theme = max(scores, key=scores.get)
        if scores[best_theme] == 0:
            # Fall back to chart_stability for general app performance comments, or trading
            if any(w in text_lower for w in ["app", "interface", "ui", "good", "nice", "simple"]):
                return "chart_stability"
            return "trading_execution"

        return best_theme

    def cluster_reviews(self, reviews: List[ReviewRecord]) -> List[ClusteredTheme]:
        """Group reviews into taxonomy themes and calculate severity-weighted scores.

        Priority Score Formula:
            Score = Total_Count + (2.5 * Negative_Count_1-2) + (1.5 * Sum_ThumbsUp)
        """
        # Bucket reviews by theme ID
        buckets: Dict[str, List[ReviewRecord]] = {theme_id: [] for theme_id in self.taxonomy}

        for r in reviews:
            theme_id = self.classify_review(r.text)
            buckets[theme_id].append(r)

        clustered_themes: List[ClusteredTheme] = []

        for theme_id, matched_reviews in buckets.items():
            meta = self.taxonomy[theme_id]
            total_count = len(matched_reviews)
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            thumbs_sum = 0
            sample_ids = []

            for r in matched_reviews:
                rating_counts[r.rating] += 1
                thumbs_sum += r.thumbs_up_count
                if len(sample_ids) < 5:
                    sample_ids.append(r.review_id)

            negative_count = rating_counts[1] + rating_counts[2]

            # Severity-weighted priority score
            priority_score = (
                (total_count * 1.0) +
                (2.5 * negative_count) +
                (1.5 * thumbs_sum)
            )

            clustered_themes.append(
                ClusteredTheme(
                    theme_id=theme_id,
                    name=meta["name"],
                    description=meta["description"],
                    review_count=total_count,
                    rating_breakdown=rating_counts,
                    thumbs_up_sum=thumbs_sum,
                    priority_score=round(priority_score, 2),
                    sample_review_ids=sample_ids,
                )
            )

        # Sort themes by priority score descending
        clustered_themes.sort(key=lambda t: t.priority_score, reverse=True)
        return clustered_themes

    def get_top_themes_and_quotes(
        self,
        reviews: List[ReviewRecord],
        top_n: int = 3
    ) -> Tuple[List[ClusteredTheme], List[VerbatimQuote]]:
        """Identify the Top 3 themes and extract exactly one verified verbatim quote per theme."""
        all_themes = self.cluster_reviews(reviews)
        top_themes = all_themes[:top_n]

        reviews_by_id = {r.review_id: r for r in reviews}
        verbatim_quotes: List[VerbatimQuote] = []

        for theme in top_themes:
            # Find the best candidate review in this theme (prioritize 1-star reviews with high detail)
            theme_reviews = [
                r for r in reviews
                if self.classify_review(r.text) == theme.theme_id
            ]

            # Sort theme reviews by rating ascending (friction first) then thumbs_up descending
            theme_reviews.sort(key=lambda r: (r.rating, -r.thumbs_up_count, -len(r.text.split())))

            selected_review = theme_reviews[0] if theme_reviews else reviews[0]

            # Extract an evocative, self-contained verbatim sentence (10-35 words)
            quote_text = QuoteVerifier.extract_verbatim_sentence(
                selected_review.text,
                preferred_keywords=self.taxonomy[theme.theme_id]["keywords"],
                min_words=8,
                max_words=35,
            )

            # Assert exact substring inclusion
            is_valid = QuoteVerifier.verify_quote_in_text(quote_text, selected_review.text)

            verbatim_quotes.append(
                VerbatimQuote(
                    review_id=selected_review.review_id,
                    user_pseudonym=selected_review.user_name_anonymized,
                    rating=selected_review.rating,
                    quote_text=quote_text,
                    theme_name=theme.name,
                    is_verified=is_valid,
                )
            )

        return top_themes, verbatim_quotes

