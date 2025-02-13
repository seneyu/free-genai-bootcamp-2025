from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class StudySessionBaseSchema:
    id: int
    activity_name: str
    group_name: str
    start_time: str
    end_time: Optional[str]
    review_items_count: int

@dataclass
class StudySessionDashboardSchema:
    id: int
    group_id: int
    created_at: str
    study_activity_id: int
    group_name: str

class StudySessionSchema:
    @staticmethod
    def basic(session) -> Dict:
        return {
            'id': session.id,
            'activity_name': session.study_activity.name if session.study_activity else None,
            'group_name': session.group.name if session.group else None,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat() if session.end_time else None,
            'review_items_count': len(session.word_reviews)
        }

    @staticmethod
    def dashboard(session) -> Dict:
        return {
            'study_session': {
                'id': session.id,
                'group_id': session.group_id,
                'created_at': session.start_time.isoformat(),
                'study_activity_id': session.study_activity_id,
                'group_name': session.group.name if session.group else None
            }
        }

    @staticmethod
    def with_pagination(sessions, page, per_page, total) -> Dict:
        return {
            'items': [StudySessionSchema.basic(session) for session in sessions],
            'pagination': {
                'current_page': page,
                'total_pages': (total + per_page - 1) // per_page,
                'total_items': total,
                'items_per_page': per_page
            }
        }