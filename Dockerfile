# Story Bible MCP — Railway/container deploy.
# Railway injects PORT; server.py honors it. Mount a volume at /data and the
# DB defaults there (STORYBIBLE_DB). STORYBIBLE_KEYS must be set in the service env.
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY server.py schema.sql ./

ENV STORYBIBLE_DB=/data/story.db
EXPOSE 8787
CMD ["python3", "server.py"]
