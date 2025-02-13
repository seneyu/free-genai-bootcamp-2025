from app.extensions import db
from app.models.word import Word
from app.models.group import Group
from app.models.study_activity import StudyActivity
from app.models.study_session import StudySession
from datetime import datetime, UTC

def create_test_data(app):
    """create test data for the test database"""
    with app.app_context():
        # create test group
        group = Group(name="Test Group")
        db.session.add(group)
        
        # create test words
        word = Word(
            french="chat",
            english="cat",
            gender="masculine",
            parts={
                "definite_article": "le",
                "indefinite_article": "un",
                "plural": "chats"
            }
        )
        db.session.add(word)
        
        # create test study activity
        activity = StudyActivity(
            name="Test Activity",
            thumbnail_url="http://example.com/thumb.jpg",
            description="Test description"
        )
        db.session.add(activity)
        
        # create test study session
        session = StudySession(
            group_id=1,
            study_activity_id=1,
            start_time=datetime.now(UTC)
        )
        db.session.add(session)
        
        db.session.commit()
        
        return {
            'group': group,
            'word': word,
            'activity': activity,
            'session': session
        } 