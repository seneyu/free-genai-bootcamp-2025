from flask import jsonify, request
from app.api import bp  # Import the blueprint from api/__init__.py
from app.extensions import db, get_or_404
from app.models.study_session import StudySession
from app.models.word_review_item import WordReviewItem
from app.schemas.study_session import StudySessionSchema
from app.schemas.word import WordSchema
from app.schemas.base import PaginationSchema
from app.models.word import Word

@bp.route('/study_sessions', methods=['GET'])
def get_study_sessions():
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(StudySession).order_by(StudySession.start_time)
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [StudySessionSchema.basic(session) for session in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })

@bp.route('/study_sessions/<int:id>', methods=['GET'])
def get_study_session(id):
    session = get_or_404(StudySession, id)
    return jsonify(StudySessionSchema.basic(session))

@bp.route('/study_sessions/<int:id>/words', methods=['GET'])
def get_study_session_words(id):
    session = get_or_404(StudySession, id)
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(Word).join(WordReviewItem)\
        .filter(WordReviewItem.study_session_id == id)
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [WordSchema.with_stats(word) for word in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })

@bp.route('/study_sessions/<int:id>/words/<int:word_id>/review', methods=['POST'])
def create_word_review(id, word_id):
    data = request.get_json()
    
    review = WordReviewItem(
        word_id=word_id,
        study_session_id=id,
        correct=data['correct']
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'word_id': review.word_id,
        'study_session_id': review.study_session_id,
        'correct': review.correct,
        'created_at': review.created_at.isoformat()
    })