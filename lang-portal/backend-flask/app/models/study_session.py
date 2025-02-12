from datetime import datetime
from app.extensions import db

class StudySession(db.Model):
    __tablename__ = 'study_sessions'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    study_activity_id = db.Column(db.Integer, db.ForeignKey('study_activities.id'))
    start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)

     # relationships
    group = db.relationship('Group', back_populates='study_sessions')
    study_activity = db.relationship('StudyActivity', back_populates='study_sessions')
    word_reviews = db.relationship('WordReviewItem', back_populates='study_session')

    def __repr__(self):
        return f'<StudySession {self.id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'activity_name': self.study_activity.name if self.study_activity else None,
            'group_name': self.group.name if self.group else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'review_items_count': len(self.word_reviews)
        }
    
    def to_dashboard_dict(self):
        return {
            'study_session': {
                'id': self.id,
                'group_id': self.group_id,
                'created_at': self.start_time.isoformat(),
                'study_activity_id': self.study_activity_id,
                'group_name': self.group.name if self.group else None
            }
        }