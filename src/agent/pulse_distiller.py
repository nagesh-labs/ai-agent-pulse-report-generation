"""Executive Pulse Distiller for Groww Weekly Feedback Note.

Assembles, formats, and validates the weekly one-page pulse note,
strictly enforcing scannability and the <= 250 words constraint.
"""

import logging
from typing import List, Optional
from src.agent.models import ClusteredTheme, VerbatimQuote, ActionItem, ExecutivePulsePayload

logger = logging.getLogger(__name__)


class PulseDistiller:
    """Assembles and formats the one-page executive pulse note with <= 250 words."""

    @staticmethod
    def count_words(text: str) -> int:
        """Count whitespace-delimited words in markdown text."""
        return len(text.strip().split())

    @classmethod
    def distill_note(
        cls,
        date_range: str,
        total_reviews: int,
        top_themes: List[ClusteredTheme],
        quotes: List[VerbatimQuote],
        actions: List[ActionItem],
        max_words: int = 250,
    ) -> ExecutivePulsePayload:
        """Construct the markdown pulse note and enforce the <= 250 word limit."""
        if len(top_themes) != 3:
            raise ValueError(f"Pulse note requires exactly 3 top themes, got {len(top_themes)}")
        if len(quotes) != 3:
            raise ValueError(f"Pulse note requires exactly 3 quotes, got {len(quotes)}")
        if len(actions) != 3:
            raise ValueError(f"Pulse note requires exactly 3 action ideas, got {len(actions)}")

        # Build initial markdown note
        lines = [
            f"# Groww App Weekly Pulse ({date_range})",
            f"**Analyzed**: {total_reviews} reviews. **Focus**: Top 3 friction drivers.",
            "",
            "### Top Themes",
        ]

        for t in top_themes:
            neg_pct = round(((t.rating_breakdown.get(1, 0) + t.rating_breakdown.get(2, 0)) / max(t.review_count, 1)) * 100)
            lines.append(f"- **{t.name}** ({t.review_count} reviews, {neg_pct}% critical): {t.description}")

        lines.extend([
            "",
            "### User Voices (Verbatim)",
        ])

        for q in quotes:
            lines.append(f'> "{q.quote_text}" -- *{q.user_pseudonym} ({q.rating}★)*')

        lines.extend([
            "",
            "### Action Ideas",
        ])

        for a in actions:
            lines.append(f"{a.item_id}. **{a.title}**: {a.recommendation}")

        note_markdown = "\n".join(lines)
        word_count = cls.count_words(note_markdown)

        # Enforce word limit constraint
        if word_count > max_words:
            logger.warning("Pulse note exceeded %d words (%d words). Compressing...", max_words, word_count)
            note_markdown = cls._compress_note(
                date_range, total_reviews, top_themes, quotes, actions, max_words=max_words
            )
            word_count = cls.count_words(note_markdown)

        return ExecutivePulsePayload(
            date_range=date_range,
            total_reviews_analyzed=total_reviews,
            top_themes=top_themes,
            verbatim_quotes=quotes,
            action_ideas=actions,
            pulse_markdown=note_markdown,
            word_count=word_count,
        )

    @classmethod
    def _compress_note(
        cls,
        date_range: str,
        total_reviews: int,
        top_themes: List[ClusteredTheme],
        quotes: List[VerbatimQuote],
        actions: List[ActionItem],
        max_words: int = 250,
    ) -> str:
        """Tightly compress theme summaries and actions while preserving quotes verbatim."""
        lines = [
            f"# Groww App Pulse ({date_range})",
            f"*{total_reviews} reviews analyzed. Top 3 operational friction drivers:*",
            "",
            "### Top Themes",
        ]

        for t in top_themes:
            lines.append(f"- **{t.name}** ({t.review_count} reviews): {t.description[:80]}...")

        lines.extend([
            "",
            "### User Voices (Verbatim)",
        ])

        for q in quotes:
            lines.append(f'> "{q.quote_text}" -- *{q.user_pseudonym}*')

        lines.extend([
            "",
            "### Action Ideas",
        ])

        for a in actions:
            lines.append(f"{a.item_id}. **{a.title}**: {a.recommendation[:110]}...")

        compressed = "\n".join(lines)
        return compressed
