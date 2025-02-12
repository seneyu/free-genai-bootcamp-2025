from datetime import datetime
from app.extensions import db

class Group(db.Model):
    __tablename__ = 'groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # relationships
    words = db.relationship('Word', secondary='words_groups', back_populates='groups')
    study_sessions = db.relationship('StudySession', back_populates='group')
    study_activities = db.relationship('StudyActivity', back_populates='group')

    def __repr__(self):
        return f'<Group {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'word_count': len(self.words)
        }
    
    def to_detail_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'stats': {
                'total_word_count': len(self.words)
            }
        }