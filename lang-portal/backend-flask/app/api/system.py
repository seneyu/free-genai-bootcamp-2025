from flask import jsonify
from app.api import bp
from app.extensions import db
from app.models.word_review_item import WordReviewItem
from app.models.study_session import StudySession
from app.database.seeds import Seeder

@bp.route('/reset_history', methods=['POST'])
def reset_history():
    try:
        # delete all word review items
        WordReviewItem.query.delete()
        # delete all study sessions
        StudySession.query.delete()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Study history has been reset'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/full_reset', methods=['POST'])
def full_reset():
    try:
        # drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # re-run seed data using Seeder class
        Seeder.seed_all()
        
        return jsonify({
            'success': True,
            'message': 'System has been fully reset'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500