# Dedicated public CODE container; no secret ever enters a build layer.
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd -u 10001 -r -s /usr/sbin/nologin adapter
COPY llm_mcp ./llm_mcp
USER 10001:10001
EXPOSE 10000
CMD ["sh", "-c", "exec uvicorn llm_mcp.server:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
