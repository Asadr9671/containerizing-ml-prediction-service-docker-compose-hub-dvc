import json
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app, FEATURES

@pytest.fixture
def client(monkeypatch):
    monkeypatch.delenv('REDIS_HOST', raising=False)
    with TestClient(app) as value:
        yield value

@pytest.fixture
def payload():
    import csv
    with open('data/raw/breast_cancer.csv') as f:
        row = next(csv.DictReader(f))
    return {key: float(row[key]) for key in FEATURES}

def test_health_and_prediction_contract(client, payload):
    assert client.get('/health').json() == {'status': 'ok'}
    response = client.post('/predict', json=payload)
    assert response.status_code == 200
    result = response.json()
    expected = app.state.model.predict_proba(np.array([[payload[k] for k in FEATURES]]))[0, list(app.state.model.classes_).index(0)]
    assert result['malignant_probability'] == pytest.approx(expected)
    assert result['label'] == ('malignant' if expected >= result['threshold'] else 'benign')
    assert client.get('/model/info').json()['feature_count'] == 30
    assert client.get('/stats').json()['counting_enabled'] is False

@pytest.mark.parametrize('value', [-1, 'wrong', None, True, '1.5'])
def test_invalid_values_rejected(client, payload, value):
    payload['mean_radius'] = value
    assert client.post('/predict', json=payload).status_code == 422

def test_missing_and_extra_fields(client, payload):
    del payload['mean_radius']
    assert client.post('/predict', json=payload).status_code == 422
    payload['mean_radius'] = 1
    payload['unknown'] = 1
    assert client.post('/predict', json=payload).status_code == 422

def test_threshold_boundary_and_redis_outage(monkeypatch, payload):
    monkeypatch.setenv('DECISION_THRESHOLD', '0')
    monkeypatch.setenv('REDIS_HOST', '127.0.0.1')
    monkeypatch.setenv('REDIS_PORT', '1')
    with TestClient(app) as client:
        assert client.post('/predict', json=payload).json()['label'] == 'malignant'
        assert client.get('/health').status_code == 200
        assert client.get('/stats').status_code == 503

def test_missing_model_fails_fast(monkeypatch):
    monkeypatch.setenv('MODEL_PATH', 'artifacts/nonexistent.joblib')
    with pytest.raises(RuntimeError, match='Model artifact missing'):
        with TestClient(app):
            pass
