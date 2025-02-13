import json
from typing import Dict

def test_reset_history(client):
    """resetting study history"""
    response = client.post('/api/reset_history')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'success' in data
    assert 'message' in data

def test_full_reset(client):
    """full system reset"""
    response = client.post('/api/full_reset')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'success' in data
    assert 'message' in data 