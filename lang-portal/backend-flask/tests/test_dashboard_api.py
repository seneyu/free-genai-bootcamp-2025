import json
from typing import Dict

def test_last_study_session(client):
    """getting last study session"""
    response = client.get('/api/dashboard/last_study_session')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'study_session' in data
    assert isinstance(data['study_session'], dict)

def test_study_progress(client):
    """getting study progress"""
    response = client.get('/api/dashboard/study_progress')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'study_progress' in data
    assert 'total_words_studied' in data['study_progress']
    assert 'total_available_words' in data['study_progress']

def test_quick_stats(client):
    """getting quick stats"""
    response = client.get('/api/dashboard/quick_stats')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'success_rate' in data
    assert 'total_study_sessions' in data
    assert 'total_active_groups' in data
    assert 'study_streak_days' in data 