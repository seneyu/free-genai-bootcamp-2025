from datetime import datetime
from app.extensions import db

class WordReviewItem(db.Model):
    __tablename__ = 'word_review_items'

    id = db.Column(db.Integer, primary_key=True)
    word_id = db.Column(db.Integer, db.ForeignKey('words.id'), nullable=False)
    study_session_id = db.Column(db.Integer, db.ForeignKey('study_sessions.id'), nullable=False)
    correct = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationships
    word = db.relationship('Word', back_populates='review_items')
    study_session = db.relationship('StudySession', back_populates='word_reviews')

    def __repr__(self):
        return f'<WordReviewItem word_id={self.word_id} correct={self.correct}>'
    
    def to_dict(self):
        return {
            'word_id': self.word_id,
            'study_session_id': self.study_session_id,
            'correct': self.correct,
            'created_at': self.created_at.isoformat()
        }