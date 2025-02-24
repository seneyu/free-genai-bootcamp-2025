import pytest
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_words(client):
    # Test GET /words endpoint
    response = client.get('/words')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'words' in data
    assert 'pagination' in data
    
    # Check word structure
    if data['words']:
        word = data['words'][0]
        assert 'french' in word
        assert 'english' in word
        assert 'gender' in word
        assert 'parts' in word

def test_get_single_word(client):
    # First create a word to test with
    new_word = {
        "french": "bonjour",
        "english": "hello",
        "gender": "verb",
        "parts": {
            "definite_article": "",
            "indefinite_article": "",
            "plural": ""
        }
    }
    create_response = client.post('/words', 
                                data=json.dumps(new_word),
                                content_type='application/json')
    assert create_response.status_code == 201
    word_id = json.loads(create_response.data)['id']
    
    # Now test GET /words/:id endpoint
    response = client.get(f'/words/{word_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'word' in data
    word = data['word']
    assert word['french'] == new_word['french']
    assert word['english'] == new_word['english']
    assert word['gender'] == new_word['gender']
    assert word['parts'] == new_word['parts']

def test_add_word(client):
    # Test POST /words endpoint
    new_word = {
        "french": "test",
        "english": "test",
        "gender": "masculine",
        "parts": {
            "definite_article": "le",
            "indefinite_article": "un",
            "plural": "tests"
        }
    }
    response = client.post('/words', 
                          data=json.dumps(new_word),
                          content_type='application/json')
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert 'id' in data