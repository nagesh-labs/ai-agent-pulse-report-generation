"""End-to-End integration test for Phase 2 Agentic Synthesis on real clean reviews."""

from pathlib import Path
from src.ingestion.models import ReviewRecord
from src.agent.llm_client import AgentSynthesisCoordinator


def test_end_to_end_phase2_synthesis():
    data_path = Path("data/processed/reviews_clean.jsonl")
    assert data_path.exists(), "reviews_clean.jsonl must exist from Phase 1"

    reviews = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                reviews.append(ReviewRecord.model_validate_json(line))

    assert len(reviews) > 0, "Clean reviews must not be empty"

    coordinator = AgentSynthesisCoordinator()
    payload = coordinator.generate_weekly_pulse(reviews)

    # Core Phase 2 assertions
    assert payload.total_reviews_analyzed == len(reviews)
    assert len(payload.top_themes) == 3
    assert len(payload.verbatim_quotes) == 3
    assert len(payload.action_ideas) == 3

    # All quotes verified
    for q in payload.verbatim_quotes:
        assert q.is_verified is True
        # Verify quote is an exact substring in the review corpus
        corpus_texts = [r.text for r in reviews]
        clean_q = " ".join(q.quote_text.strip().split()).lower()
        found = any(clean_q in " ".join(t.strip().split()).lower() for t in corpus_texts)
        assert found is True, f"Quote must exist in corpus: {q.quote_text}"

    # Strict <= 250 word count
    assert payload.word_count <= 250

    # Formatted markdown verification
    assert "# Groww App" in payload.pulse_markdown
    assert "### Top Themes" in payload.pulse_markdown
    assert "### User Voices" in payload.pulse_markdown
    assert "### Action Ideas" in payload.pulse_markdown


def test_groq_llm_action_synthesis_mock(mocker):
    """Verify that Groq LLM response is parsed and incorporated when API returns actions."""
    mock_groq_response = mocker.MagicMock()
    mock_groq_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(
                content='''{
                    "actions": [
                        {"item_id": 1, "title": "Upgrade Order Execution Engine", "recommendation": "Deploy zero-loss state cache.", "target_theme": "Trading & Order Execution"},
                        {"item_id": 2, "title": "Automate CAMS Sync", "recommendation": "Run daily statement reconciliation.", "target_theme": "Portfolio Tracking"},
                        {"item_id": 3, "title": "Enhance Chart Caching", "recommendation": "Cache symbol candlesticks locally.", "target_theme": "Chart Stability"}
                    ]
                }'''
            )
        )
    ]

    coordinator = AgentSynthesisCoordinator(api_key="mock_groq_key")
    coordinator.groq_client = mocker.MagicMock()
    coordinator.groq_client.chat.completions.create.return_value = mock_groq_response

    from src.agent.clusterer import ThematicClusterer
    from src.ingestion.models import ReviewRecord
    from datetime import datetime

    sample_reviews = [
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
            text="CAMS statement mismatch and mutual funds display wrong XIRR.",
            date=datetime.now(),
            thumbs_up_count=5,
        ),
        ReviewRecord(
            review_id="r3",
            user_name_anonymized="Reviewer #0003",
            rating=2,
            text="Charts are not opening and showing failed to load in network.",
            date=datetime.now(),
            thumbs_up_count=1,
        ),
    ]

    payload = coordinator.generate_weekly_pulse(sample_reviews)

    assert payload.word_count <= 250
    assert len(payload.action_ideas) == 3
    assert payload.action_ideas[0].title == "Upgrade Order Execution Engine"
    assert "Upgrade Order Execution Engine" in payload.pulse_markdown

