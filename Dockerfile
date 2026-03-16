FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create volume mount point for persistent SQLite database
RUN mkdir -p /data
ENV DB_PATH=/data/assistant.db

EXPOSE 8080

# Use gunicorn for production with a single worker (SQLite isn't concurrent-friendly)
CMD ["sh", "-c", "python -c 'from state.database import init_db; init_db()' && gunicorn -w 1 -b 0.0.0.0:${PORT:-8080} --timeout 120 bot.whatsapp_bot:app"]
