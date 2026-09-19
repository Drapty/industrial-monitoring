from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_sensor_ingestion():
    payload = {
        'topic': 'industrial/sensors/line-1/motor-a',
        'payload': {
            'temperature': 75,
            'pressure': 90,
            'vibration': 3.8,
            'humidity': 48,
            'timestamp': '2025-01-01T00:00:00Z',
        },
    }
    response = client.post('/api/sensor', json=payload)
    assert response.status_code == 200
    assert response.json()['status'] == 'accepted'


def test_snapshot_returns_data():
    response = client.get('/api/snapshot')
    assert response.status_code == 200
    data = response.json()
    assert 'sensors' in data
    assert 'alerts' in data
    assert 'history' in data
