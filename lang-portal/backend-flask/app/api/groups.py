from flask import Blueprint, jsonify, request
from app.api import bp
from app.models.group import Group
from app.models.word import Word
from app.models.study_session import StudySession
from app.schemas.group import GroupSchema
from app.schemas.word import WordSchema
from app.schemas.study_session import StudySessionSchema
from app.schemas.base import PaginationSchema
from app.extensions import db, get_or_404

@bp.route('/groups', methods=['GET'])
def get_groups():
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(Group)
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [GroupSchema.basic(group) for group in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })

@bp.route('/groups/<int:id>', methods=['GET'])
def get_group(id):
    group = get_or_404(Group, id)
    return jsonify(GroupSchema.detail(group))

@bp.route('/groups/<int:id>/words', methods=['GET'])
def get_group_words(id):
    group = get_or_404(Group, id)
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(Word).join(Word.groups).filter(Group.id == id)
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [WordSchema.with_stats(word) for word in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })

@bp.route('/groups/<int:id>/study_sessions', methods=['GET'])
def get_group_study_sessions(id):
    group = get_or_404(Group, id)
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(StudySession).filter_by(group_id=id)
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [StudySessionSchema.basic(session) for session in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })