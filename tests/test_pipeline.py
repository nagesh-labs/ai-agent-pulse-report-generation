"""Integration tests for Phase 4 Pipeline Orchestration."""

from unittest.mock import MagicMock
from pathlib import Path
from src.pipeline import GrowwPulsePipeline
from src.ingestion.models import ReviewRecord


def test_pipeline_dry_run_execution():
    """Verify that GrowwPulsePipeline executes end-to-end cleanly in dry-run mode."""
    mock_mcp = MagicMock()
    mock_mcp.call_tool.return_value = {"status": "success", "summary": "Delivered successfully"}

    pipeline = GrowwPulsePipeline(mcp_client=mock_mcp)
    result = pipeline.run(scrape_fresh=False, dry_run=True)

    assert result["status"] == "completed"
    assert result["reviews_analyzed"] > 0
    assert result["word_count"] <= 250
    assert result["themes_count"] == 3
    assert result["quotes_count"] == 3
    assert result["actions_count"] == 3
    assert "Groww App Pulse" in result["pulse_markdown"]
    assert result["google_doc_result"]["status"] == "success"
    assert result["gmail_result"]["status"] == "success"

