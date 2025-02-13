import json
from typing import Dict

def test_get_words(client):
    """getting words list"""
    response = client.get('/api/words')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'items' in data
    assert 'pagination' in data

def test_get_word(client):
    """getting single word"""
    response = client.get('/api/words/1')
    assert response.status_code == 200
    data: Dict = json.loads(response.data)
    assert 'french' in data
    assert 'english' in data
    assert 'gender' in data
    assert 'parts' in data
    assert 'stats' in data
    assert 'groups' in data 