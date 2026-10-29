# Breast Cancer Triage API

Educational FastAPI screening-support demo using the scikit-learn breast-cancer
dataset, a reproducible seed-42 training pipeline and DVC-tracked data. Not a medical
device. Malignant is target 0 and is the positive class for reported probability.

Release tags: `1.0.0` and `latest` point to the same production image.

```sh
docker run -d --name triage -p 8000:8000 asad3390/breast-cancer-triage-api:1.0.0
```

Open http://localhost:8000/docs to send all 30 nonnegative numeric features to
`POST /predict`. Also available: `/health`, `/model/info`, `/stats`. Container port:
8000. Standalone mode does not require Redis.

For Compose, download `docker-compose.hub.yml` and `.env.example` from
https://github.com/Asadr9671/containerizing-ml-prediction-service-docker-compose-hub-dvc,
rename `.env.example` to `.env`, then run:

```sh
docker compose -f docker-compose.hub.yml up -d --wait
```

Configuration: `MODEL_PATH=artifacts/model.joblib`, `DECISION_THRESHOLD=0.5`,
`LOG_LEVEL=INFO`, optional `REDIS_HOST`, `REDIS_PORT=6379`. Build provenance is exposed
through `MODEL_VERSION` and `GIT_SHA`. Compose additionally uses
`DOCKERHUB_USERNAME=asad3390`, `IMAGE_TAG=1.0.0`, and `API_PORT=8000`.
Redis counts successful predictions; inference continues during Redis outages.
The image runs as non-root UID 10001 and includes a `/health` healthcheck.
