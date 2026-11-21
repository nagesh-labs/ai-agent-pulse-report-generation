"""Unit and integration tests for Phase 3 MCP Tool Integration Layer."""

import pytest
from unittest.mock import MagicMock
from src.mcp.client import VercelMCPClient, MCPClientError
from src.mcp.docs_tool import GoogleDocsTool
from src.mcp.gmail_tool import GmailTool


def test_vercel_mcp_live_health_check():
    """Verify that the deployed Vercel MCP server is live, healthy, and exposes the expected tools."""
    client = VercelMCPClient()
    health_data = client.check_health()

    assert health_data.get("status") == "healthy"
    assert health_data.get("service") == "google-workspace-mcp"
    assert "send_gmail" in health_data.get("tools", [])
    assert "append_to_google_doc" in health_data.get("tools", [])


def test_mcp_client_mock_execution():
    """Verify client behavior in mock/dry-run mode."""
    client = VercelMCPClient()

    # Docs append mock
    res_docs = client.call_tool("append_to_google_doc", {"document_id": "test_doc_123", "content": "Hello"}, dry_run=True)
    assert res_docs["status"] == "success"
    assert "test_doc_123" in res_docs["summary"]
    assert "https://docs.google.com/document/d/test_doc_123/edit" in res_docs["document_url"]

    # Gmail send mock
    res_gmail = client.call_tool("send_gmail", {"to": "test@groww.in", "subject": "Pulse", "body": "Summary"}, dry_run=True)
    assert res_gmail["status"] == "success"
    assert "test@groww.in" in res_gmail["summary"]


def test_docs_tool_url_extraction_and_payload():
    """Verify that GoogleDocsTool parses full URLs into doc IDs and formats entries."""
    mock_client = MagicMock()
    mock_client.call_tool.return_value = {"status": "success", "summary": "Appended"}

    docs_tool = GoogleDocsTool(mcp_client=mock_client)
    full_url = "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit"

    result = docs_tool.append_pulse(
        content="# Pulse Note\nTop themes here.",
        document_id=full_url,
        dry_run=True,
    )

    assert result["document_id"] == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    assert "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit" == result["document_url"]

    # Check mock call arguments
    mock_client.call_tool.assert_called_once()
    call_args = mock_client.call_tool.call_args[1]
    assert call_args["tool_name"] == "append_to_google_doc"
    assert call_args["arguments"]["document_id"] == "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
    assert "GROWW APP FEEDBACK PULSE" in call_args["arguments"]["content"]


def test_gmail_tool_validation_and_payload():
    """Verify Gmail recipient validation and message formatting."""
    mock_client = MagicMock()
    mock_client.call_tool.return_value = {"status": "success", "summary": "Sent"}

    gmail_tool = GmailTool(mcp_client=mock_client)

    # Invalid recipient raises MCPClientError
    with pytest.raises(MCPClientError):
        gmail_tool.send_pulse_email(content="Pulse", recipient="invalid-email-address")

    # Valid execution
    result = gmail_tool.send_pulse_email(
        content="# Weekly Pulse\nAll is well.",
        recipient="product-team@groww.in",
        date_range="Oct 21 - Oct 31, 2026",
        google_doc_url="https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit",
        dry_run=True,
    )

    assert result["recipient"] == "product-team@groww.in"
    assert "Oct 21 - Oct 31, 2026" in result["subject"]

    mock_client.call_tool.assert_called_once()
    call_args = mock_client.call_tool.call_args[1]
    assert call_args["tool_name"] == "send_gmail"
    assert call_args["arguments"]["to"] == "product-team@groww.in"
    assert "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit" in call_args["arguments"]["body"]

