import json
from typing import Dict

def test_get_study_sessions(client):
    """getting study sessions list"""
    response = client.get('/api/study_sessions')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data

def test_get_study_session(client):
    """getting single study session"""
    response = client.get('/api/study_sessions/1')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'id' in data
    assert 'activity_name' in data
    assert 'group_name' in data

def test_get_study_session_words(client):
    """getting words in a study session"""
    response = client.get('/api/study_sessions/1/words')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data 