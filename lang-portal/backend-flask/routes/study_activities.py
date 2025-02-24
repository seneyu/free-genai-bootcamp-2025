from flask import jsonify, request
from flask_cors import cross_origin
import math

def load(app):
    @app.route('/api/study-activities', methods=['GET', 'OPTIONS'])
    @cross_origin()
    def get_study_activities():
        try:
            cursor = app.db.cursor()
            cursor.execute('SELECT id, name, url, preview_url FROM study_activities')
            activities = cursor.fetchall()
            
            return jsonify([{
                'id': activity['id'],
                'title': activity['name'],
                'launch_url': activity['url'],
                'preview_url': activity['preview_url']
            } for activity in activities])
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/study-activities/<int:id>', methods=['GET', 'OPTIONS'])
    @cross_origin()
    def get_study_activity(id):
        try:
            cursor = app.db.cursor()
            cursor.execute('''
                SELECT id, name, thumbnail_url, description 
                FROM study_activities 
                WHERE id = ?
            ''', (id,))
            activity = cursor.fetchone()
            
            if not activity:
                return jsonify({'error': 'Activity not found'}), 404
                
            return jsonify({
                'id': activity['id'],
                'name': activity['name'],
                'thumbnail_url': activity['thumbnail_url'],
                'description': activity['description']
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/study-activities/<int:id>/study-sessions', methods=['GET', 'OPTIONS'])
    @cross_origin()
    def get_study_activity_sessions(id):
        cursor = app.db.cursor()
        
        # Verify activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Activity not found'}), 404

        # Get paginated sessions (100 items per page)
        page = request.args.get('page', 1, type=int)
        per_page = 100
        offset = (page - 1) * per_page

        # Get total count
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM study_sessions ss
            WHERE ss.study_activity_id = ?
        ''', (id,))
        total_count = cursor.fetchone()['count']

        # Get paginated sessions
        cursor.execute('''
            SELECT 
                ss.id,
                sa.name as activity_name,
                g.name as group_name,
                ss.start_time,
                ss.end_time,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.study_activity_id = ?
            GROUP BY ss.id, sa.name, g.name, ss.start_time, ss.end_time
            ORDER BY ss.start_time DESC
            LIMIT ? OFFSET ?
        ''', (id, per_page, offset))
        sessions = cursor.fetchall()

        return jsonify({
            'items': [{
                'id': session['id'],
                'activity_name': session['activity_name'],
                'group_name': session['group_name'],
                'start_time': session['start_time'],
                'end_time': session['end_time'],
                'review_items_count': session['review_items_count']
            } for session in sessions]
        })

    @app.route('/api/study-activities/<int:id>/launch', methods=['GET', 'OPTIONS'])
    @cross_origin()
    def get_study_activity_launch_data(id):
        cursor = app.db.cursor()
        
        # Get activity details
        cursor.execute('SELECT id, name, url, preview_url FROM study_activities WHERE id = ?', (id,))
        activity = cursor.fetchone()
        
        if not activity:
            return jsonify({'error': 'Activity not found'}), 404
        
        # Get available groups
        cursor.execute('SELECT id, name FROM groups')
        groups = cursor.fetchall()
        
        return jsonify({
            'activity': {
                'id': activity['id'],
                'title': activity['name'],
                'launch_url': activity['url'],
                'preview_url': activity['preview_url']
            },
            'groups': [{
                'id': group['id'],
                'name': group['name']
            } for group in groups]
        })

    @app.route('/api/study-activities/<int:id>/sessions', methods=['GET', 'OPTIONS'])
    @cross_origin()
    def get_study_activity_sessions_legacy(id):
        cursor = app.db.cursor()
        
        # Verify activity exists
        cursor.execute('SELECT id FROM study_activities WHERE id = ?', (id,))
        if not cursor.fetchone():
            return jsonify({'error': 'Activity not found'}), 404

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page

        # Get total count
        cursor.execute('''
            SELECT COUNT(*) as count 
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            WHERE ss.study_activity_id = ?
        ''', (id,))
        total_count = cursor.fetchone()['count']

        # Get paginated sessions
        cursor.execute('''
            SELECT 
                ss.id,
                ss.group_id,
                g.name as group_name,
                sa.name as activity_name,
                ss.created_at,
                ss.study_activity_id as activity_id,
                COUNT(wri.id) as review_items_count
            FROM study_sessions ss
            JOIN groups g ON g.id = ss.group_id
            JOIN study_activities sa ON sa.id = ss.study_activity_id
            LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
            WHERE ss.study_activity_id = ?
            GROUP BY ss.id, ss.group_id, g.name, sa.name, ss.created_at, ss.study_activity_id
            ORDER BY ss.created_at DESC
            LIMIT ? OFFSET ?
        ''', (id, per_page, offset))
        sessions = cursor.fetchall()

        return jsonify({
            'items': [{
                'id': session['id'],
                'group_id': session['group_id'],
                'group_name': session['group_name'],
                'activity_id': session['activity_id'],
                'activity_name': session['activity_name'],
                'start_time': session['created_at'],
                'end_time': session['created_at'],  # For now, just use the same time since we don't track end time
                'review_items_count': session['review_items_count']
            } for session in sessions],
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': math.ceil(total_count / per_page)
        })
