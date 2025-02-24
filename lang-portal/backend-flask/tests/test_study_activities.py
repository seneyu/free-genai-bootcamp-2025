def test_get_study_activity(client):
    # Test getting an existing activity
    response = client.get('/api/study_activities/1')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'id' in data
    assert 'name' in data
    assert 'thumbnail_url' in data
    assert 'description' in data
    assert data['name'] == 'Vocabulary Quiz'
    
    # Test getting a non-existent activity
    response = client.get('/api/study_activities/999')
    assert response.status_code == 404

def test_get_study_activity_sessions(client):
    # Test getting sessions for an existing activity
    response = client.get('/api/study_activities/1/study_sessions')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'items' in data
    
    items = data['items']
    assert len(items) == 2  # Based on test data
    
    session = items[0]
    assert 'id' in session
    assert 'activity_name' in session
    assert 'group_name' in session
    assert 'start_time' in session
    assert 'end_time' in session
    assert 'review_items_count' in session
    
    # Test getting sessions for a non-existent activity
    response = client.get('/api/study_activities/999/study_sessions')
    assert response.status_code == 404

def test_study_sessions_pagination(client):
    # Add more test sessions to test pagination
    # This test might need to be adjusted based on your actual pagination implementation
    response = client.get('/api/study_activities/1/study_sessions?page=1')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'items' in data
    assert len(data['items']) <= 100  # Should not exceed items per page
