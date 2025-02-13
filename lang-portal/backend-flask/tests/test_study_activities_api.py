import json
from typing import Dict

def test_get_study_activity(client):
    """getting a single study activity"""
    response = client.get('/api/study_activities/1')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'id' in data
    assert 'name' in data
    assert 'thumbnail_url' in data
    assert 'description' in data

def test_get_study_activity_sessions(client):
    """getting study sessions for an activity"""
    response = client.get('/api/study_activities/1/study_sessions')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data

def test_create_study_activity(client):
    """creating a new study activity session"""
    payload = {
        'group_id': 1,
        'study_activity_id': 1
    }
    response = client.post('/api/study_activities', 
                          data=json.dumps(payload),
                          content_type='application/json')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'id' in data
    assert 'group_id' in data 