import json
import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated
import joblib
import numpy as np
import redis
from fastapi import FastAPI, HTTPException
from pydantic import ConfigDict, Field, create_model

# Dataset order is explicit so validation does not require training data/packages.
BASE = ['radius', 'texture', 'perimeter', 'area', 'smoothness', 'compactness', 'concavity', 'concave_points', 'symmetry', 'fractal_dimension']
FEATURES = ['mean_' + x for x in BASE] + [x + '_error' for x in BASE] + ['worst_' + x for x in BASE]
Record = create_model('Record', __config__=ConfigDict(extra='forbid'),
                      **{name: (Annotated[float, Field(ge=0, allow_inf_nan=False, strict=True)], ...) for name in FEATURES})
logger = logging.getLogger('triage')

@asynccontextmanager
async def lifespan(app):
    level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(level=level, stream=sys.stdout, force=True, format='%(levelname)s %(message)s')
    threshold = float(os.getenv('DECISION_THRESHOLD', '0.5'))
    if not 0 <= threshold <= 1:
        raise ValueError('DECISION_THRESHOLD must be between 0 and 1')
    path = Path(os.getenv('MODEL_PATH', 'artifacts/model.joblib'))
    if not path.is_file():
        logger.error('Model artifact missing: %s; run training or rebuild the image', path)
        raise RuntimeError(f'Model artifact missing: {path}')
    app.state.model = joblib.load(path)
    app.state.card = json.loads(path.with_name('model_card.json').read_text())
    if app.state.card['feature_names'] != FEATURES:
        raise RuntimeError('Model feature order does not match API contract')
    app.state.threshold = threshold
    host = os.getenv('REDIS_HOST')
    app.state.redis = redis.Redis(host=host, port=int(os.getenv('REDIS_PORT', '6379')),
                                  socket_connect_timeout=0.3, socket_timeout=0.3) if host else None
    logger.info('Model loaded once: %s; threshold=%s; LOG_LEVEL=%s', path, threshold, level)
    yield
    if app.state.redis:
        app.state.redis.close()

app = FastAPI(title='Meridian Diagnostics - Educational Triage API', version='1.0.0', lifespan=lifespan)

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.post('/predict')
def predict(record: Record):
    values = record.model_dump()
    model = app.state.model
    probability = float(model.predict_proba(np.array([[values[name] for name in FEATURES]]))[0, list(model.classes_).index(0)])
    if app.state.redis:
        try:
            app.state.redis.incr('predictions')
        except redis.RedisError as error:
            logger.warning('Redis counter unavailable; prediction still served: %s', error)
    return {'label': 'malignant' if probability >= app.state.threshold else 'benign',
            'malignant_probability': probability, 'threshold': app.state.threshold,
            'model_version': os.getenv('MODEL_VERSION', app.state.card['model_version'])}

@app.get('/model/info')
def model_info():
    card = app.state.card
    return {**card, 'model_version': os.getenv('MODEL_VERSION', card['model_version']),
            'git_commit': os.getenv('GIT_SHA', card['git_commit']), 'decision_threshold': app.state.threshold}

@app.get('/stats')
def stats():
    if app.state.redis is None:
        return {'predictions': 0, 'counting_enabled': False}
    try:
        return {'predictions': int(app.state.redis.get('predictions') or 0), 'counting_enabled': True}
    except redis.RedisError:
        raise HTTPException(status_code=503, detail='Prediction counter unavailable')
