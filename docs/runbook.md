# Operational Runbook: Interactive Web Dashboard & Railway Deployment

This guide covers running the **Groww Mobile App Feedback Pulse** high-fidelity executive dashboard locally, deploying it to **Railway**, and triggering delivery via Web UI or GitHub Actions.

---

## 1. High-Fidelity Executive Dashboard Overview

The dashboard (`src/web.py` + `src/templates/index.html`), designed according to Google Stitch ("Executive Emerald Pulse" theme), provides an executive command center for the feedback pulse agent:
- **Real-Time KPIs**: Total clean reviews (187), critical friction volume (1-2★, 48.7%), positive praise (5★, 35.8%), and word count adherence ($\le 250$ words, 94% capacity).
- **Executive Pulse Workspace**: Complete weekly executive note preview with Top 3 Friction Themes, Verbatim Quotations, Action Ideas, and a raw markdown toggle.
- **Live Toolchain Dispatch Cards**: Direct status indicators and links to Google Docs (`AI Agent Report ↗`) and Gmail (`nagesh14423@gmail.com`).
- **Live MCP Terminal Stream**: Real-time console showing SSE handshakes, tool executions, and latency metrics.
- **Thematic Analytics & Donut Charts**: Ranked domain themes with composite severity bars and an interactive SVG rating breakdown donut.
- **PII-Sanitized Corpus Explorer**: Full client-side searchable table of 187 clean reviews with star rating filter chips.

### Local Dashboard Testing
Run the executive dashboard locally from your project directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn src.web:app --host 0.0.0.0 --port 8501
```
Open your browser at `http://localhost:8501`.

*(Note: The legacy Streamlit interface remains accessible via `.\.venv\Scripts\streamlit.exe run src/app.py` if desired).*

---

## 2. Deploying to Cloud (Render / Railway)

The application runs in a production Docker container using the included `Dockerfile` and `render.yaml` (or `railway.json`).

```mermaid
flowchart LR
    A["GitHub Repo<br/>(Main Branch)"] --> B["Render Web Service<br/>(Docker Build • Free Tier)"]
    B --> C["FastAPI Uvicorn Container<br/>(Port: $PORT)"]
    C --> D["Vercel MCP Server<br/>(ai-agent-mcp-server.vercel.app)"]
    D --> E["Google Docs & Gmail"]
```

### Method A: Deploy on Render Free Tier (Recommended)

1. **Sign in to Render**:
   - Go to [dashboard.render.com](https://dashboard.render.com) and log in with GitHub.
   - Click **+ New** $\to$ Select **Web Service**.
   - Choose `ai-agent-pulse-report-generation` repository.

2. **Configure Service Details**:
   - **Runtime**: `Docker`
   - **Instance Type**: `Free` ($0/mo, 512MB RAM, 750 free hours/month)
   - **Health Check Path**: `/health`

3. **Configure Environment Variables in Render**:
   - In the **Environment Variables** section, add:

| Variable Name | Example Value | Purpose |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | `gsk_...` | Groq Cloud API Key for Llama 3.3 70B |
| `MCP_AUTH_KEY` | `nagesh` | Master key for Vercel MCP server |
| `GOOGLE_DOC_ID` | `1chaQkkUovsVC7OGYM1HOSiPPFGW3bdcuOKSm6eLopSM` | Target Google Doc ID |
| `PULSE_EMAIL_RECIPIENT` | `nagesh14423@gmail.com` | Target recipient email address |
| `MCP_SERVER_URL` | `https://ai-agent-mcp-server.vercel.app/sse` | MCP SSE endpoint |
| `MCP_HEALTH_URL` | `https://ai-agent-mcp-server.vercel.app/health` | MCP Health endpoint |

4. **Deploy**:
   - Click **Create Web Service**.
   - Render will build the container and provide a live URL like `https://groww-feedback-pulse.onrender.com`.

---

### Method B: Deploy via Render Blueprint (`render.yaml`)

- Connect repository at [dashboard.render.com/blueprints](https://dashboard.render.com/blueprints). Render uses `render.yaml` to auto-configure the service and environment variables in 1 click!

---

### Method C: Deploy via Railway (Alternative)

If you prefer using the command line:

```powershell
# 1. Install Railway CLI (via npm or scoop/brew)
npm i -g @railway/cli

# 2. Login to Railway
railway login

# 3. Link and Deploy
railway init
railway up
```

---

## 3. On-Demand Execution via GitHub Actions (Alternative)

If you also want to run the pipeline without opening the web dashboard:
1. Open your GitHub repository $\to$ **Actions** tab.
2. Select **"Generate Groww Feedback Pulse"**.
3. Click **Run workflow**.

---

## 4. Local CLI Execution (Alternative)

```powershell
# Run using cached reviews
.\.venv\Scripts\python.exe -m src.pipeline

# Run with live scraping from Play Store
.\.venv\Scripts\python.exe -m src.pipeline --scrape --weeks 10

# Run in dry-run mode
.\.venv\Scripts\python.exe -m src.pipeline --dry-run
```
