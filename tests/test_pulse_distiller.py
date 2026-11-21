"""Unit tests for PulseDistiller and <= 250 word count constraint."""

from src.agent.models import ClusteredTheme, VerbatimQuote, ActionItem
from src.agent.pulse_distiller import PulseDistiller


def test_pulse_distiller_word_count_compliance():
    themes = [
        ClusteredTheme(
            theme_id="t1",
            name="Trading & Order Execution",
            description="Stop-loss drops and exit button freezes during peak volatility.",
            review_count=82,
            rating_breakdown={1: 70, 2: 12},
        ),
        ClusteredTheme(
            theme_id="t2",
            name="Portfolio Tracking & MF Sync",
            description="CAMS statement sync failures and incorrect negative XIRR.",
            review_count=35,
            rating_breakdown={1: 25, 2: 10},
        ),
        ClusteredTheme(
            theme_id="t3",
            name="Chart Performance & Stability",
            description="Charts failing to load and Android line preview disparity.",
            review_count=30,
            rating_breakdown={1: 15, 2: 10, 3: 5},
        ),
    ]

    quotes = [
        VerbatimQuote(
            review_id="r1",
            user_pseudonym="Reviewer #0001",
            rating=1,
            quote_text="Stop loss not triggered during market fall and lost 30000 rupees.",
            theme_name="Trading & Order Execution",
            is_verified=True,
        ),
        VerbatimQuote(
            review_id="r2",
            user_pseudonym="Reviewer #0002",
            rating=1,
            quote_text="CAMS statement mismatch and mutual funds display wrong XIRR.",
            theme_name="Portfolio Tracking & MF Sync",
            is_verified=True,
        ),
        VerbatimQuote(
            review_id="r3",
            user_pseudonym="Reviewer #0003",
            rating=2,
            quote_text="Charts are not opening and showing failed to load in network.",
            theme_name="Chart Performance & Stability",
            is_verified=True,
        ),
    ]

    actions = [
        ActionItem(
            item_id=1,
            title="Harden F&O Order Exit Resiliency",
            recommendation="Implement client websocket heartbeat reconnection to prevent adapter errors.",
            target_theme="Trading & Order Execution",
        ),
        ActionItem(
            item_id=2,
            title="Automate CAMS Reconciliation",
            recommendation="Deploy automated daily CAMS ingestion reconciliation to fix XIRR bugs.",
            target_theme="Portfolio Tracking & MF Sync",
        ),
        ActionItem(
            item_id=3,
            title="Resolve Chart Loading Timeouts",
            recommendation="Cache symbol candlestick data locally to eliminate failed-to-load errors.",
            target_theme="Chart Performance & Stability",
        ),
    ]

    payload = PulseDistiller.distill_note(
        date_range="Aug 23, 2026 - Nov 01, 2026",
        total_reviews=187,
        top_themes=themes,
        quotes=quotes,
        actions=actions,
        max_words=250,
    )

    # Word count must strictly be <= 250 words
    assert payload.word_count <= 250
    assert len(payload.top_themes) == 3
    assert len(payload.verbatim_quotes) == 3
    assert len(payload.action_ideas) == 3

    # All quotes must be in the markdown note
    for q in quotes:
        assert q.quote_text in payload.pulse_markdown

