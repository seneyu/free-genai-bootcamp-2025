import json
from typing import Dict

def test_get_groups(client):
    """getting groups list"""
    response = client.get('/api/groups')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data

def test_get_group(client):
    """getting single group"""
    response = client.get('/api/groups/1')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'id' in data
    assert 'name' in data
    assert 'stats' in data

def test_get_group_words(client):
    """getting words in a group"""
    response = client.get('/api/groups/1/words')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data

def test_get_group_study_sessions(client):
    """getting study sessions for a group"""
    response = client.get('/api/groups/1/study_sessions')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data 