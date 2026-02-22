FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (Playwright for URL/web scanning)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Optional: Install Playwright browsers for URL scan (JS-rendered crawl). Skip if not needed.
RUN playwright install chromium 2>/dev/null || true

# Copy application code
COPY . .

# Create chroma data directory
RUN mkdir -p chroma_data

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
