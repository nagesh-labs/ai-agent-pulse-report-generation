"""Google Docs MCP Tool Adapter for appending weekly pulse notes.

Invokes the 'append_to_google_doc' tool on the Vercel MCP server.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.mcp.client import VercelMCPClient, MCPClientError

logger = logging.getLogger(__name__)


class GoogleDocsTool:
    """Manages appending weekly pulse notes to Google Docs via MCP."""

    def __init__(self, mcp_client: Optional[VercelMCPClient] = None) -> None:
        self.mcp_client = mcp_client or VercelMCPClient()

    def append_pulse(
        self,
        content: str,
        document_id: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Format and append the weekly pulse note to an authorized Google Doc.

        Args:
            content: The markdown or plain-text pulse note content.
            document_id: The target Google Doc ID or URL.
            dry_run: If True, simulates execution without network calls.

        Returns:
            Dict[str, Any]: Execution status, summary, and document URL.
        """
        doc_id = document_id or os.environ.get("GOOGLE_DOC_ID") or settings.delivery.google_doc_id
        if not doc_id or not doc_id.strip():
            raise MCPClientError("Target Google Doc ID is required.")

        # Clean document ID if a full URL was provided
        if "/document/d/" in doc_id:
            doc_id = doc_id.split("/document/d/")[1].split("/")[0]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_entry = (
            f"\n\n{'='*70}\n"
            f"GROWW APP FEEDBACK PULSE -- GENERATED ON {timestamp}\n"
            f"{'='*70}\n\n"
            f"{content.strip()}\n"
        )

        logger.info("Appending pulse note to Google Doc ID '%s'...", doc_id)
        result = self.mcp_client.call_tool(
            tool_name="append_to_google_doc",
            arguments={
                "document_id": doc_id,
                "content": formatted_entry,
            },
            dry_run=dry_run,
        )

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        result["document_id"] = doc_id
        result["document_url"] = doc_url
        return result

