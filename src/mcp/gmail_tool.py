"""Gmail MCP Tool Adapter for dispatching weekly pulse emails.

Invokes the 'send_gmail' tool on the Vercel MCP server.
"""

import re
import logging
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.mcp.client import VercelMCPClient, MCPClientError

logger = logging.getLogger(__name__)


class GmailTool:
    """Manages dispatching pulse emails through the user's Gmail account via MCP."""

    _EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

    def __init__(self, mcp_client: Optional[VercelMCPClient] = None) -> None:
        self.mcp_client = mcp_client or VercelMCPClient()

    def validate_recipient(self, recipient: str) -> str:
        """Validate email format."""
        clean = (recipient or "").strip()
        if not clean or not self._EMAIL_REGEX.match(clean):
            raise MCPClientError(f"Invalid recipient email address: '{recipient}'")
        return clean

    def send_pulse_email(
        self,
        content: str,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        google_doc_url: Optional[str] = None,
        date_range: Optional[str] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Dispatch the weekly pulse email to the designated recipient.

        Args:
            content: The text of the pulse note.
            recipient: Target recipient email.
            subject: Optional custom subject line.
            google_doc_url: Optional web URL to the Google Doc for reference.
            date_range: Timeframe string for subject line.
            dry_run: If True, simulates execution without network calls.

        Returns:
            Dict[str, Any]: Dispatch status and message summary.
        """
        to_email = self.validate_recipient(recipient or os.environ.get("PULSE_EMAIL_RECIPIENT") or settings.delivery.email_recipient)

        if not subject:
            dr_str = f" ({date_range})" if date_range else ""
            subject = f"{settings.delivery.pulse_title_prefix}{dr_str}"

        # Construct email body with Google Doc pointer
        body_parts = [
            content.strip(),
            "\n" + "-"*50,
        ]

        if google_doc_url:
            body_parts.append(f"View and collaborate on the full Google Doc:\n{google_doc_url}")
        else:
            body_parts.append("Note: Generated autonomously by Groww Mobile App Feedback Pulse Agent.")

        full_body = "\n\n".join(body_parts)

        logger.info("Sending pulse email to '%s' with subject '%s'...", to_email, subject)
        result = self.mcp_client.call_tool(
            tool_name="send_gmail",
            arguments={
                "to": to_email,
                "subject": subject,
                "body": full_body,
            },
            dry_run=dry_run,
        )

        result["recipient"] = to_email
        result["subject"] = subject
        return result

