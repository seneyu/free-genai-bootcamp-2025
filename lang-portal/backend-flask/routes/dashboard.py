from flask import jsonify
from flask_cors import cross_origin
from datetime import datetime, timedelta

def load(app):
    @app.route('/api/dashboard/last-study-session', methods=['GET'])
    @cross_origin()
    def get_last_study_session():
        try:
            cursor = app.db.cursor()
            
            # Get the most recent study session
            cursor.execute('''
                SELECT 
                    ss.id,
                    ss.group_id,
                    g.name as group_name,
                    ss.start_time as created_at,
                    ss.activity_id,
                    sa.name as activity_name
                FROM study_sessions ss
                LEFT JOIN groups g ON ss.group_id = g.id
                LEFT JOIN study_activities sa ON ss.activity_id = sa.id
                ORDER BY ss.start_time DESC
                LIMIT 1
            ''')
            
            session = cursor.fetchone()
            
            if not session:
                return jsonify({"study_session": None})
            
            return jsonify({
                "study_session": {
                    "id": session["id"],
                    "group_id": session["group_id"],
                    "created_at": session["created_at"],
                    "activity_id": session["activity_id"],
                    "group_name": session["group_name"],
                    "activity_name": session["activity_name"]
                }
            })
            
        except Exception as e:
            app.logger.error(f"Error in get_last_study_session: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/dashboard/study-progress', methods=['GET'])
    @cross_origin()
    def get_study_progress():
        try:
            cursor = app.db.cursor()
            
            # Get total words studied (unique words that have been reviewed)
            cursor.execute('''
                SELECT COUNT(DISTINCT word_id) as total_studied
                FROM word_review_items
            ''')
            result = cursor.fetchone()
            total_studied = result["total_studied"] if result else 0
            
            # Get total available words
            cursor.execute('SELECT COUNT(*) as total FROM words')
            result = cursor.fetchone()
            total_available = result["total"] if result else 0
            
            return jsonify({
                "study_progress": {
                    "total_words_studied": total_studied,
                    "total_available_words": total_available
                }
            })
            
        except Exception as e:
            app.logger.error(f"Error in get_study_progress: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    @app.route('/api/dashboard/quick-stats', methods=['GET'])
    @cross_origin()
    def get_quick_stats():
        try:
            cursor = app.db.cursor()
            
            # Get total words studied (unique words that have been reviewed)
            cursor.execute('''
                SELECT COUNT(DISTINCT word_id) as total_words_studied
                FROM word_review_items
            ''')
            total_words_studied = cursor.fetchone()['total_words_studied']
            
            # Get total study sessions
            cursor.execute('''
                SELECT COUNT(*) as total_sessions
                FROM study_sessions
            ''')
            total_sessions = cursor.fetchone()['total_sessions']
            
            # Get success rate
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_reviews
                FROM word_review_items
            ''')
            review_stats = cursor.fetchone()
            success_rate = 0
            if review_stats['total_reviews'] > 0:
                success_rate = (review_stats['correct_reviews'] / review_stats['total_reviews']) * 100
            
            return jsonify({
                "total_words_studied": total_words_studied,
                "total_sessions": total_sessions,
                "success_rate": round(success_rate, 1)
            })
            
        except Exception as e:
            app.logger.error(f"Error in get_quick_stats: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500
