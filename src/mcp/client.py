"""MCP Client for remote Vercel-deployed Google Workspace MCP Server.

Connects via Server-Sent Events (SSE) transport with Bearer token authentication
to invoke 'send_gmail' and 'append_to_google_doc' tools.
"""

import os
import logging
from typing import Dict, Any, Optional
import httpx
from mcp.client.sse import sse_client
from mcp import ClientSession

from src.config.settings import settings

logger = logging.getLogger(__name__)


class MCPClientError(Exception):
    """Raised when an MCP connection or tool invocation fails."""
    pass


class VercelMCPClient:
    """Manages SSE connections and tool execution on the remote Vercel MCP server."""

    def __init__(
        self,
        server_url: Optional[str] = None,
        health_url: Optional[str] = None,
        auth_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.server_url = server_url or settings.mcp.server_url
        self.health_url = health_url or settings.mcp.health_url
        self.auth_key = auth_key or settings.mcp.auth_key
        self.timeout = timeout or settings.mcp.timeout_seconds

    def check_health(self) -> Dict[str, Any]:
        """Perform a pre-flight health and diagnostic check against the server's /health endpoint."""
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(self.health_url)
                if res.status_code == 200:
                    data = res.json()
                    logger.info("Vercel MCP Server health check: %s (version: %s)", data.get("status"), data.get("version"))
                    return data
                else:
                    raise MCPClientError(f"Health check failed with HTTP {res.status_code}: {res.text}")
        except Exception as e:
            logger.error("Failed to connect to MCP health endpoint at %s: %s", self.health_url, e)
            raise MCPClientError(f"Cannot connect to MCP server: {e}") from e

    async def call_tool_async(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute an MCP tool over SSE connection."""
        if dry_run or not self.auth_key:
            if not self.auth_key and not dry_run:
                logger.warning("MCP_AUTH_KEY is not configured in environment. Operating in mock/dry-run mode.")
            return self._mock_tool_execution(tool_name, arguments)

        headers = {
            "Authorization": f"Bearer {self.auth_key}",
            "User-Agent": "Groww-Feedback-Pulse-Agent/1.0",
        }

        max_attempts = 3
        last_error = None
        for attempt in range(1, max_attempts + 1):
            logger.info("Connecting to MCP SSE endpoint %s to call tool '%s' (attempt %d/%d)...", self.server_url, tool_name, attempt, max_attempts)
            is_err = False
            summary = ""
            result = None
            try:
                async with sse_client(self.server_url, headers=headers, timeout=self.timeout) as (read_stream, write_stream):
                    async with ClientSession(read_stream, write_stream) as session:
                        await session.initialize()
                        result = await session.call_tool(tool_name, arguments=arguments)

                        text_outputs = []
                        is_err = getattr(result, "is_error", False)
                        for content_item in getattr(result, "content", []):
                            if hasattr(content_item, "text"):
                                text_outputs.append(content_item.text)

                        summary = "\n".join(text_outputs) if text_outputs else str(result)
                
                if is_err:
                    raise MCPClientError(f"Tool '{tool_name}' returned an error: {summary}")

                return {
                    "status": "success",
                    "tool": tool_name,
                    "summary": summary,
                    "raw_result": str(result),
                }
            except MCPClientError:
                # Logical errors returned by server tools should not be retried
                raise
            except Exception as e:
                last_error = e
                logger.warning("MCP SSE attempt %d failed: %s", attempt, e)
                if attempt < max_attempts:
                    import anyio
                    await anyio.sleep(1.0 * attempt)

        logger.error("MCP tool invocation '%s' failed after %d attempts: %s", tool_name, max_attempts, last_error)
        raise MCPClientError(f"MCP tool call error: {last_error}") from last_error

    def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Synchronous wrapper around async tool execution."""
        import anyio
        return anyio.run(self.call_tool_async, tool_name, arguments, dry_run)

    def _mock_tool_execution(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic mock response for offline testing or when auth key is pending."""
        logger.info("[MOCK] Simulated execution for tool '%s'", tool_name)
        if tool_name == "append_to_google_doc":
            doc_id = arguments.get("document_id", "mock_doc_id")
            return {
                "status": "success",
                "tool": tool_name,
                "summary": f"Content appended successfully to Google Doc (ID: {doc_id}).",
                "document_url": f"https://docs.google.com/document/d/{doc_id}/edit",
            }
        elif tool_name == "send_gmail":
            to = arguments.get("to", "user@example.com")
            subject = arguments.get("subject", "Pulse")
            return {
                "status": "success",
                "tool": tool_name,
                "summary": f"Email sent successfully to {to}. Subject: '{subject}'.",
                "message_id": "mock_msg_18b2938472",
            }
        else:
            return {
                "status": "success",
                "tool": tool_name,
                "summary": f"Tool '{tool_name}' executed successfully in mock mode.",
            }

