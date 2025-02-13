from datetime import datetime, UTC
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.extensions import db

class WordReviewItem(db.Model):
    __tablename__ = 'word_review_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    word_id: Mapped[int] = mapped_column(ForeignKey('words.id'), nullable=False)
    study_session_id: Mapped[int] = mapped_column(ForeignKey('study_sessions.id'), nullable=False)
    correct: Mapped[bool] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    # relationships
    word = relationship('Word', back_populates='review_items')
    study_session = relationship('StudySession', back_populates='word_reviews')

    def __repr__(self):
        return f'<WordReviewItem word_id={self.word_id} correct={self.correct}>'
    
    def to_dict(self):
        return {
            'word_id': self.word_id,
            'study_session_id': self.study_session_id,
            'correct': self.correct,
            'created_at': self.created_at.isoformat()
        }