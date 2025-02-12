from datetime import datetime
from app.extensions import db

class StudyActivity(db.Model):
    __tablename__ = 'study_activities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    thumbnail_url = db.Column(db.String(255))
    description = db.Column(db.Text)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    study_sessions = db.relationship(
        'StudySession', 
        back_populates='study_activity',
        foreign_keys='StudySession.study_activity_id'
    )
    group = db.relationship('Group', back_populates='study_activities')

    def __repr__(self):
        return f'<StudyActivity {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'thumbnail_url': self.thumbnail_url,
            'description': self.description
        }