# Production Dockerfile for Groww Feedback Pulse AI Agent & Streamlit Dashboard
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501

WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source, data, config, and documentation
COPY . .

# Expose port (Render dynamic PORT or local default 8501)
EXPOSE 8501
EXPOSE 10000

# Run healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT:-8501}/health || exit 1

# Launch FastAPI web application
CMD ["sh", "-c", "uvicorn src.web:app --host 0.0.0.0 --port ${PORT:-8501}"]
