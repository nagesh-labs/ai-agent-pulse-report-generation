"""High-Fidelity FastAPI Web Server for Groww Mobile App Feedback Pulse Dashboard.

Serves the executive dashboard designed in Google Stitch with live MCP toolchain
orchestration, review corpus exploration, and dynamic weekly synthesis.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

# Ensure repo root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.config.settings import settings
from src.pipeline import GrowwPulsePipeline
from src.ingestion.models import ReviewRecord
from src.agent.clusterer import ThematicClusterer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("groww_web")

app = FastAPI(
    title="Groww Feedback Pulse Executive Dashboard",
    description="Real-time telemetry, semantic clustering, and MCP delivery for Groww product leaders.",
    version="2.8.4",
)

TEMPLATES_DIR = ROOT_DIR / "src" / "templates"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


class SynthesizeRequest(BaseModel):
    scrape_fresh: bool = False
    weeks_back: int = Field(default=10, ge=1, le=52)
    dry_run: bool = False
    doc_id: Optional[str] = None
    recipient_email: Optional[str] = None


@app.get("/health")
@app.get("/_stcore/health")
async def health_check():
    """Universal healthcheck for Railway, Docker, and uptime monitoring."""
    return {"status": "healthy", "service": "groww-feedback-pulse", "version": "2.8.4"}


@app.get("/_stcore/host-config")
@app.get("/_stcore/allowed-message-origins")
async def stcore_compat():
    """Compatibility handler for residual browser tab polling."""
    return {"allowedOrigins": [], "useExternalAuthToken": False}


@app.get("/api/health")
async def api_health():
    """MCP agent and environment connectivity telemetry."""
    mcp_url = settings.mcp.server_url or os.getenv("MCP_SERVER_URL", "https://ai-agent-mcp-server.vercel.app/sse")
    target_doc = os.getenv("GOOGLE_DOC_ID") or settings.delivery.google_doc_id
    target_email = os.getenv("PULSE_EMAIL_RECIPIENT") or settings.delivery.email_recipient

    clean_file = ROOT_DIR / "data" / "processed" / "reviews_clean.jsonl"
    corpus_count = 0
    if clean_file.exists():
        with open(clean_file, "r", encoding="utf-8") as f:
            corpus_count = sum(1 for line in f if line.strip())

    return {
        "status": "online",
        "mcp_server": mcp_url,
        "google_doc_id": target_doc,
        "recipient_email": target_email,
        "corpus_count": corpus_count,
        "groq_configured": bool(os.getenv("GROQ_API_KEY") or settings.agent.api_key),
    }


@app.get("/api/reviews")
async def get_reviews():
    """Returns the full sanitized review corpus and aggregate stats."""
    clean_file = ROOT_DIR / "data" / "processed" / "reviews_clean.jsonl"
    if not clean_file.exists():
        raise HTTPException(status_code=404, detail="Clean review corpus not found.")

    reviews: List[Dict[str, Any]] = []
    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}

    with open(clean_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rec = ReviewRecord.model_validate_json(line)
                r_dict = rec.model_dump()
                r_dict["date"] = rec.date.strftime("%Y-%m-%d")
                reviews.append(r_dict)
                rating_counts[rec.rating] = rating_counts.get(rec.rating, 0) + 1

    total = len(reviews)
    critical_friction = rating_counts[1] + rating_counts[2]
    positive_praise = rating_counts[5]

    return {
        "total": total,
        "critical_friction": critical_friction,
        "critical_friction_pct": round((critical_friction / total * 100), 1) if total else 0,
        "positive_praise": positive_praise,
        "positive_praise_pct": round((positive_praise / total * 100), 1) if total else 0,
        "rating_breakdown": rating_counts,
        "reviews": reviews,
    }


@app.get("/api/initial-data")
async def get_initial_data():
    """Returns initial data for dashboard metrics, themes, and configuration."""
    clean_file = ROOT_DIR / "data" / "processed" / "reviews_clean.jsonl"
    records: List[ReviewRecord] = []
    if clean_file.exists():
        with open(clean_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(ReviewRecord.model_validate_json(line))

    clusterer = ThematicClusterer()
    clustered_themes = clusterer.cluster_reviews(records)
    themes_data = [t.model_dump() for t in clustered_themes]

    rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for r in records:
        rating_counts[r.rating] = rating_counts.get(r.rating, 0) + 1

    total = len(records)
    target_doc = os.getenv("GOOGLE_DOC_ID") or settings.delivery.google_doc_id
    target_email = os.getenv("PULSE_EMAIL_RECIPIENT") or settings.delivery.email_recipient

    return {
        "total_reviews": total,
        "critical_friction": rating_counts[1] + rating_counts[2],
        "critical_friction_pct": round(((rating_counts[1] + rating_counts[2]) / total * 100), 1) if total else 0,
        "positive_praise": rating_counts[5],
        "positive_praise_pct": round((rating_counts[5] / total * 100), 1) if total else 0,
        "rating_breakdown": rating_counts,
        "themes": themes_data,
        "target_doc_id": target_doc,
        "target_doc_url": f"https://docs.google.com/document/d/{target_doc}/edit",
        "target_email": target_email,
        "max_words": settings.agent.max_word_count,
    }


@app.post("/api/synthesize")
async def run_synthesis(payload: SynthesizeRequest):
    """Executes the complete feedback pulse pipeline and delivers to Google Workspace & Gmail."""
    try:
        import asyncio
        pipeline = GrowwPulsePipeline()
        # Offload synchronous execution (which calls anyio.run internally) to a worker thread
        result = await asyncio.to_thread(
            pipeline.run,
            scrape_fresh=payload.scrape_fresh,
            weeks_back=payload.weeks_back,
            dry_run=payload.dry_run,
            doc_id=payload.doc_id,
            recipient_email=payload.recipient_email,
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.exception("Synthesis failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Renders the executive dashboard template."""
    target_doc = os.getenv("GOOGLE_DOC_ID") or settings.delivery.google_doc_id
    target_email = os.getenv("PULSE_EMAIL_RECIPIENT") or settings.delivery.email_recipient
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "target_doc_id": target_doc,
            "target_doc_url": f"https://docs.google.com/document/d/{target_doc}/edit",
            "target_email": target_email,
        },
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8501))
    uvicorn.run("src.web:app", host="0.0.0.0", port=port, reload=False)
