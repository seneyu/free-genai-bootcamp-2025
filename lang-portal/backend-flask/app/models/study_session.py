from datetime import datetime, UTC
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
from app.extensions import db

class StudySession(db.Model):
    __tablename__ = 'study_sessions'

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey('groups.id'))
    study_activity_id: Mapped[int] = mapped_column(ForeignKey('study_activities.id'))
    start_time: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    end_time: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # relationships
    group = relationship('Group', back_populates='study_sessions')
    study_activity = relationship('StudyActivity', back_populates='study_sessions')
    word_reviews = relationship('WordReviewItem', back_populates='study_session')

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