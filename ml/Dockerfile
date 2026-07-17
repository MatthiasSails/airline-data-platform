FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    WEB_CONCURRENCY=1

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY api/ ./api/
COPY src/ ./src/
COPY models/ ./models/

# Run as a non-root user
RUN groupadd --system appuser \
    && useradd --system --gid appuser --no-create-home appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# WEB_CONCURRENCY controls the number of uvicorn worker processes; override
# with `docker run -e WEB_CONCURRENCY=4 ...` to scale on a bigger VM.
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers ${WEB_CONCURRENCY}"]
