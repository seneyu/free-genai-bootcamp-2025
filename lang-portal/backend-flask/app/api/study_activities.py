from flask import jsonify, request
from app.api import bp
from app.extensions import db, get_or_404
from app.models.study_activity import StudyActivity
from app.models.study_session import StudySession
from app.schemas.study_activity import StudyActivitySchema
from app.schemas.study_session import StudySessionSchema
from app.schemas.base import PaginationSchema

@bp.route('/study_activities/<int:id>', methods=['GET'])
def get_study_activity(id):
    activity = get_or_404(StudyActivity, id)
    return jsonify(StudyActivitySchema.from_model(activity))

@bp.route('/study_activities/<int:id>/study_sessions', methods=['GET'])
def get_study_activity_sessions(id):
    activity = get_or_404(StudyActivity, id)
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(StudySession).filter_by(study_activity_id=id)
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [StudySessionSchema.basic(session) for session in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })

@bp.route('/study_activities', methods=['POST'])
def create_study_activity():
    data = request.get_json()
    
    study_session = StudySession(
        group_id=data['group_id'],
        study_activity_id=data['study_activity_id']
    )
    
    db.session.add(study_session)
    db.session.commit()
    
    return jsonify({
        'id': study_session.id,
        'group_id': study_session.group_id
    })