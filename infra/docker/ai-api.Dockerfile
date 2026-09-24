FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY packages/protocol packages/protocol
COPY packages/shared packages/shared
COPY services/ai-api services/ai-api

RUN pip install --no-cache-dir \
    -e packages/protocol \
    -e packages/shared \
    -e "services/ai-api[dev]"

ENV AI_PLATFORM_ENV=development
ENV AI_PLATFORM_MODEL_PROVIDER=development_mock

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "ai_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
