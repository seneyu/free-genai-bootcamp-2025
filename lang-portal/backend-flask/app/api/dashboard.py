from flask import jsonify
from app.api import bp
from app.extensions import db
from app.models.study_session import StudySession
from app.models.word import Word
from app.models.word_review_item import WordReviewItem
from app.models.group import Group
from app.schemas.study_session import StudySessionSchema
from sqlalchemy import func, distinct
from datetime import datetime, timedelta, UTC

@bp.route('/dashboard/last_study_session', methods=['GET'])
def get_last_study_session():
    stmt = db.select(StudySession).order_by(StudySession.start_time.desc())
    last_session = db.session.execute(stmt).scalar_one_or_none()
    if not last_session:
        return jsonify({'study_session': None})
    return jsonify(StudySessionSchema.dashboard(last_session))

@bp.route('/dashboard/study_progress', methods=['GET'])
def get_study_progress():
    total_available = db.session.scalar(db.select(func.count()).select_from(Word))
    total_studied = db.session.scalar(
        db.select(func.count(distinct(WordReviewItem.word_id)))
    )
    
    return jsonify({
        'study_progress': {
            'total_words_studied': total_studied,
            'total_available_words': total_available
        }
    })

@bp.route('/dashboard/quick_stats', methods=['GET'])
def get_quick_stats():
    # calculate success rate
    total_reviews = db.session.scalar(db.select(func.count()).select_from(WordReviewItem))
    if total_reviews > 0:
        correct_reviews = db.session.scalar(
            db.select(func.count())
            .select_from(WordReviewItem)
            .filter_by(correct=True)
        )
        success_rate = (correct_reviews / total_reviews) * 100
    else:
        success_rate = 0

    # count study sessions and active groups
    total_study_sessions = db.session.scalar(db.select(func.count()).select_from(StudySession))
    total_active_groups = db.session.scalar(db.select(func.count()).select_from(Group))

    # calculate study streak
    today = datetime.now(UTC).date()
    streak = 0
    current_date = today

    while True:
        has_session = db.session.scalar(
            db.select(StudySession)
            .filter(func.date(StudySession.start_time) == current_date)
        ) is not None
        
        if not has_session:
            break
            
        streak += 1
        current_date -= timedelta(days=1)

    return jsonify({
        'success_rate': round(success_rate, 1),
        'total_study_sessions': total_study_sessions,
        'total_active_groups': total_active_groups,
        'study_streak_days': streak
    })