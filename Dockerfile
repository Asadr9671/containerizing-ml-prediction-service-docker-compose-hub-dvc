FROM python:3.12.10-slim-bookworm AS trainer
WORKDIR /build
COPY requirements-train.txt .
RUN pip install --no-cache-dir -r requirements-train.txt
COPY training/ training/
COPY params.yaml .
COPY data/raw/breast_cancer.csv data/raw/breast_cancer.csv
ARG MODEL_VERSION=1.0.0
ARG GIT_SHA=local
ENV GIT_SHA=${GIT_SHA}
RUN python -m training.train --model-version ${MODEL_VERSION}

FROM python:3.12.10-slim-bookworm AS runtime
WORKDIR /app
COPY requirements-serve.txt .
RUN pip install --no-cache-dir -r requirements-serve.txt && useradd --uid 10001 --create-home appuser
COPY --from=trainer --chown=10001:10001 /build/artifacts/ artifacts/
COPY --chown=10001:10001 app/ app/
ARG MODEL_VERSION=1.0.0
ARG GIT_SHA=local
ENV MODEL_VERSION=${MODEL_VERSION} GIT_SHA=${GIT_SHA} MODEL_PATH=artifacts/model.joblib DECISION_THRESHOLD=0.5 LOG_LEVEL=INFO REDIS_PORT=6379 PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
LABEL org.opencontainers.image.version=${MODEL_VERSION} org.opencontainers.image.revision=${GIT_SHA}
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=5s --timeout=3s --start-period=15s --retries=5 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
ENTRYPOINT ["python", "-m", "app.server"]
CMD ["--host", "0.0.0.0", "--port", "8000"]
