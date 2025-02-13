from flask import jsonify, request
from app.api import bp
from app.extensions import db, get_or_404  # Add get_or_404
from app.models.word import Word
from app.schemas.word import WordSchema
from app.schemas.base import PaginationSchema

@bp.route('/words', methods=['GET'])
def get_words():
    page = request.args.get('page', 1, type=int)
    per_page = 100
    
    stmt = db.select(Word)  # Use select()
    pagination = db.paginate(stmt, page=page, per_page=per_page)
    
    return jsonify({
        'items': [WordSchema.with_stats(word) for word in pagination.items],
        'pagination': PaginationSchema.create(page, per_page, pagination.total)
    })

@bp.route('/words/<int:id>', methods=['GET'])
def get_word(id):
    word = get_or_404(Word, id)  # Use get_or_404 helper
    return jsonify(WordSchema.detail(word))