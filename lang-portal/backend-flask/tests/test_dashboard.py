def test_last_study_session(client):
    response = client.get('/api/dashboard/last_study_session')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'study_session' in data
    
    session = data['study_session']
    assert session is not None
    assert 'id' in session
    assert 'group_id' in session
    assert 'created_at' in session
    assert 'study_activity_id' in session
    assert 'group_name' in session

def test_study_progress(client):
    response = client.get('/api/dashboard/study_progress')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'study_progress' in data
    
    progress = data['study_progress']
    assert 'total_words_studied' in progress
    assert 'total_available_words' in progress
    assert progress['total_words_studied'] == 2  # Based on test data
    assert progress['total_available_words'] == 2  # Based on test data

def test_quick_stats(client):
    response = client.get('/api/dashboard/quick_stats')
    assert response.status_code == 200
    
    data = response.get_json()
    assert 'success_rate' in data
    assert 'total_study_sessions' in data
    assert 'total_active_groups' in data
    assert 'study_streak_days' in data
    
    # Based on our test data:
    assert data['total_study_sessions'] == 3
    assert data['success_rate'] == 66.7  # 2 correct out of 3 reviews
    assert data['total_active_groups'] == 2
    assert data['study_streak_days'] >= 1  # At least 1 day streak
