"""Manual end-to-end test script to verify MCP delivery via Vercel MCP Server.

Executes:
1. Load clean Groww reviews (Phase 1).
2. Synthesize weekly pulse report (Phase 2).
3. Append report to Google Doc via MCP tool 'append_to_google_doc'.
4. Send report email via MCP tool 'send_gmail' to recipient.
"""

import os
import sys
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

# Ensure stdout handles UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("manual_test")

from src.ingestion.models import ReviewRecord
from src.agent.llm_client import AgentSynthesisCoordinator
from src.mcp.client import VercelMCPClient
from src.mcp.docs_tool import GoogleDocsTool
from src.mcp.gmail_tool import GmailTool


def main():
    print("=" * 80)
    print("GROWW FEEDBACK PULSE - LIVE MCP DELIVERY TEST")
    print("=" * 80)

    # 1. Environment & MCP Pre-flight Check
    auth_key = os.getenv("MCP_AUTH_KEY")
    doc_id = os.getenv("GOOGLE_DOC_ID")
    email_to = os.getenv("PULSE_EMAIL_RECIPIENT")

    print(f"\n[1] Configuration Check:")
    print(f"    - MCP Server URL : https://ai-agent-mcp-server.vercel.app/sse")
    print(f"    - MCP_AUTH_KEY   : {'Configured (' + auth_key[:3] + '***)' if auth_key else 'MISSING'}")
    print(f"    - Target Doc ID  : {doc_id}")
    print(f"    - Email Recipient: {email_to}")

    client = VercelMCPClient()
    health = client.check_health()
    print(f"    - Health Status  : {health.get('status')} (tools: {health.get('tools')})")

    # 2. Load Reviews
    data_path = Path("data/processed/reviews_clean.jsonl")
    if not data_path.exists():
        print(f"Error: {data_path} not found.")
        sys.exit(1)

    reviews = []
    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                reviews.append(ReviewRecord.model_validate_json(line))

    print(f"\n[2] Loaded {len(reviews)} clean English reviews from {data_path}")

    # 3. Synthesize Pulse Note
    print("\n[3] Synthesizing Weekly Pulse Note...")
    coordinator = AgentSynthesisCoordinator()
    payload = coordinator.generate_weekly_pulse(reviews)

    print("\n" + "-" * 60)
    print("SYNTHESIZED WEEKLY PULSE REPORT:")
    print("-" * 60)
    print(payload.pulse_markdown)
    print("-" * 60)
    print(f"Word Count: {payload.word_count} words (Limit: <= 250 words)\n")

    # 4. Invoke append_to_google_doc via MCP
    print("\n[4] Invoking MCP Tool: 'append_to_google_doc'...")
    docs_tool = GoogleDocsTool(mcp_client=client)
    try:
        docs_res = docs_tool.append_pulse(
            content=payload.pulse_markdown,
            document_id=doc_id,
            dry_run=False,
        )
        print(f"    >> Google Docs Result: {docs_res.get('status')}")
        print(f"    >> Summary: {docs_res.get('summary')}")
        print(f"    >> Document URL: {docs_res.get('document_url')}")
    except Exception as e:
        print(f"    >> ERROR in append_to_google_doc: {e}")
        docs_res = {"document_url": f"https://docs.google.com/document/d/{doc_id}/edit"}

    # 5. Invoke send_gmail via MCP
    print("\n[5] Invoking MCP Tool: 'send_gmail'...")
    gmail_tool = GmailTool(mcp_client=client)
    try:
        doc_url = docs_res.get("document_url", f"https://docs.google.com/document/d/{doc_id}/edit")
        gmail_res = gmail_tool.send_pulse_email(
            content=payload.pulse_markdown,
            recipient=email_to,
            google_doc_url=doc_url,
            date_range=payload.date_range,
            dry_run=False,
        )
        print(f"    >> Gmail Result: {gmail_res.get('status')}")
        print(f"    >> Summary: {gmail_res.get('summary')}")
        print(f"    >> Sent to: {gmail_res.get('recipient')}")
    except Exception as e:
        print(f"    >> ERROR in send_gmail: {e}")

    print("\n" + "=" * 80)
    print("MANUAL TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()

