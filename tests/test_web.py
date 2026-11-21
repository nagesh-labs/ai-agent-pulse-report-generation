"""Integration tests for the Executive Web Dashboard FastAPI endpoints."""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from src.web import app


client = TestClient(app)


def test_health_endpoints():
    """Verify standard and legacy healthcheck endpoints."""
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/_stcore/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "healthy"


def test_api_health_endpoint():
    """Verify MCP connectivity and telemetry endpoint."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert "mcp_server" in data
    assert data["corpus_count"] > 0


def test_api_reviews_endpoint():
    """Verify reviews API returns full sanitized corpus and metrics."""
    res = client.get("/api/reviews")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 187
    assert data["critical_friction"] > 0
    assert data["positive_praise"] > 0
    assert len(data["reviews"]) == 187
    assert "rating_breakdown" in data
    assert data["rating_breakdown"]["1"] >= 1


def test_api_initial_data_endpoint():
    """Verify initial telemetry and domain clustering themes."""
    res = client.get("/api/initial-data")
    assert res.status_code == 200
    data = res.json()
    assert data["total_reviews"] == 187
    assert len(data["themes"]) <= 5
    assert "target_doc_url" in data
    assert "target_email" in data


def test_dashboard_html_rendering():
    """Verify root GET / renders the complete Stitch executive UI."""
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    html = res.text
    assert "Groww Feedback Pulse" in html
    assert "dispatch-pulse-btn" in html
    assert "tab-content-severity" in html
    assert "corpus-table-body" in html


def test_api_synthesize_dry_run():
    """Verify synthesis execution via API in dry run mode."""
    with patch("src.pipeline.GoogleDocsTool.append_pulse") as mock_docs, \
         patch("src.pipeline.GmailTool.send_pulse_email") as mock_gmail:
        mock_docs.return_value = {"status": "success", "summary": "Appended to Doc"}
        mock_gmail.return_value = {"status": "success", "summary": "Sent email", "message_id": "test-msg-123"}

        payload = {
            "scrape_fresh": False,
            "weeks_back": 10,
            "dry_run": True,
        }
        res = client.post("/api/synthesize", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "completed"
        assert data["word_count"] <= 250
        assert len(data["top_themes"]) == 3
        assert len(data["verbatim_quotes"]) == 3
        assert len(data["action_ideas"]) == 3
        assert "Groww App Pulse" in data["pulse_markdown"]
