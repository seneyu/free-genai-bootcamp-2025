from flask import request, jsonify, g
from flask_cors import cross_origin
from datetime import datetime
import math

def load(app):
  # todo /study_sessions POST
    @app.route('/api/study-sessions', methods=['POST'])
    @cross_origin()
    def create_study_session():
      try:
        data = request.get_json()
        
        if not data:
          return jsonify({"error": "No data provided"}), 400
        
        # Extract required fields
        group_id = data.get('group_id')
        activity_id = data.get('activity_id')
        study_activity_id = data.get('study_activity_id')
        
        # Use either activity_id or study_activity_id based on what was provided
        activity_id = activity_id or study_activity_id or 2  # Default to 2 for Writing Practice
        
        if not group_id:
          return jsonify({"error": "group_id is required"}), 400
        
        # Get current timestamp
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = app.db.cursor()
        
        # Insert the new study session with start_time
        cursor.execute('''
          INSERT INTO study_sessions (group_id, activity_id, start_time)
          VALUES (?, ?, ?)
        ''', (group_id, activity_id, current_time))
        
        session_id = cursor.lastrowid
        app.db.commit()
        
        # Return the created session
        return jsonify({
          "session_id": session_id,
          "id": session_id,
          "group_id": group_id,
          "activity_id": activity_id,
          "start_time": current_time,
          "message": "Study session created successfully"
        }), 201
        
      except Exception as e:
        app.db.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500

    @app.route('/api/study-sessions', methods=['GET'])
    @cross_origin()
    def get_study_sessions():
      try:
        cursor = app.db.cursor()
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page
        print(f"Query params: page={page}, per_page={per_page}")

        # Debug: Check table structure
        print("Checking tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        table_names = [table['name'] for table in tables]
        print(f"Tables in database: {table_names}")

        # Check study_sessions structure
        print("Checking study_sessions table...")
        cursor.execute("PRAGMA table_info(study_sessions)")
        columns = cursor.fetchall()
        print(f"study_sessions columns: {[col['name'] for col in columns]}")
        
        # Check study_activities structure
        print("Checking study_activities table...")
        cursor.execute("PRAGMA table_info(study_activities)")
        columns = cursor.fetchall()
        print(f"study_activities columns: {[col['name'] for col in columns]}")

        # Check if there are any study sessions
        cursor.execute("SELECT COUNT(*) as count FROM study_sessions")
        count = cursor.fetchone()['count']
        print(f"Number of study sessions in database: {count}")
        
        # Get filter parameters
        group_id = request.args.get('group_id')
        active = request.args.get('active', '').lower() in ['true', '1', 't', 'yes']
        print(f"Filter params: group_id={group_id}, active={active}")
        
        # Base query
        base_query = '''
          FROM study_sessions ss
          JOIN groups g ON g.id = ss.group_id
          JOIN study_activities sa ON sa.id = ss.activity_id
        '''

        # Add filters
        where_clauses = []
        query_params = []
        
        if group_id:
            where_clauses.append('ss.group_id = ?')
            query_params.append(group_id)
        
        if active:
            # Define active as sessions created within the last 24 hours
            where_clauses.append("ss.start_time >= datetime('now', '-1 day')")
        
        # Construct the WHERE clause if any filters were added
        where_clause = ''
        if where_clauses:
            where_clause = ' WHERE ' + ' AND '.join(where_clauses)
        
        # Get total count
        count_query = f'SELECT COUNT(*) as count {base_query}{where_clause}'
        print(f"Count query: {count_query} with params {query_params}")
        cursor.execute(count_query, query_params)
        total_count = cursor.fetchone()['count']
        print(f"Total count: {total_count}")
        
        # Get paginated sessions
        full_query = f'''
          SELECT 
            ss.id,
            ss.group_id,
            g.name as group_name,
            sa.id as activity_id,
            sa.name as activity_name,
            ss.start_time,
            ss.end_time,
            COUNT(wri.id) as review_items_count,
            SUM(CASE WHEN wri.is_correct = 1 THEN 1 ELSE 0 END) as correct_count
          {base_query}
          LEFT JOIN word_review_items wri ON wri.session_id = ss.id
          {where_clause}
          GROUP BY ss.id, ss.group_id, g.name, sa.id, sa.name, ss.start_time, ss.end_time
          ORDER BY ss.start_time DESC
          LIMIT ? OFFSET ?
        '''
        
        # Add pagination parameters to the query
        final_params = query_params.copy()
        final_params.extend([per_page, offset])
        print(f"Full query: {full_query} with params {final_params}")
        
        cursor.execute(full_query, final_params)
        sessions = cursor.fetchall()
        print(f"Found {len(sessions)} sessions")

        # Calculate total pages
        total_pages = math.ceil(total_count / per_page)
        print(f"Total pages: {total_pages}")

        response_data = {
          'study_sessions': [{
            'id': session['id'],
            'group_id': session['group_id'],
            'group_name': session['group_name'],
            'activity_id': session['activity_id'],
            'activity_name': session['activity_name'],
            'start_time': session['start_time'],
            'end_time': session['end_time'] if 'end_time' in session.keys() else None,  # Safely access end_time
            'review_items_count': session['review_items_count'],
            'correct_count': session['correct_count']
          } for session in sessions],
          'total_pages': total_pages,
          'current_page': page
        }
        
        print(f"Returning response with {len(response_data['study_sessions'])} sessions")
        return jsonify(response_data)
        
      except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in get_study_sessions: {str(e)}")
        print(f"Traceback: {error_trace}")
        return jsonify({"error": str(e), "trace": error_trace}), 500

    @app.route('/api/study-sessions/<id>', methods=['GET'])
    @cross_origin()
    def get_study_session(id):
      try:
        cursor = app.db.cursor()
        
        # Get session details
        cursor.execute('''
          SELECT 
            ss.id,
            ss.group_id,
            g.name as group_name,
            sa.id as activity_id,
            sa.name as activity_name,
            ss.created_at,
            COUNT(wri.id) as review_items_count
          FROM study_sessions ss
          JOIN groups g ON g.id = ss.group_id
          JOIN study_activities sa ON sa.id = ss.study_activity_id
          LEFT JOIN word_review_items wri ON wri.study_session_id = ss.id
          WHERE ss.id = ?
          GROUP BY ss.id
        ''', (id,))
        
        session = cursor.fetchone()
        if not session:
          return jsonify({"error": "Study session not found"}), 404

        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        offset = (page - 1) * per_page

        # Get the words reviewed in this session with their review status
        cursor.execute('''
          SELECT 
            w.*,
            COALESCE(SUM(CASE WHEN wri.correct = 1 THEN 1 ELSE 0 END), 0) as session_correct_count,
            COALESCE(SUM(CASE WHEN wri.correct = 0 THEN 1 ELSE 0 END), 0) as session_wrong_count
          FROM words w
          JOIN word_review_items wri ON wri.word_id = w.id
          WHERE wri.study_session_id = ?
          GROUP BY w.id
          ORDER BY w.kanji
          LIMIT ? OFFSET ?
        ''', (id, per_page, offset))
        
        words = cursor.fetchall()

        # Get total count of words
        cursor.execute('''
          SELECT COUNT(DISTINCT w.id) as count
          FROM words w
          JOIN word_review_items wri ON wri.word_id = w.id
          WHERE wri.study_session_id = ?
        ''', (id,))
        
        total_count = cursor.fetchone()['count']

        return jsonify({
          'session': {
            'id': session['id'],
            'group_id': session['group_id'],
            'group_name': session['group_name'],
            'activity_id': session['activity_id'],
            'activity_name': session['activity_name'],
            'start_time': session['created_at'],
            'end_time': session['created_at'],  # For now, just use the same time
            'review_items_count': session['review_items_count']
          },
          'words': [{
            'id': word['id'],
            'kanji': word['kanji'],
            'romaji': word['romaji'],
            'english': word['english'],
            'correct_count': word['session_correct_count'],
            'wrong_count': word['session_wrong_count']
          } for word in words],
          'total': total_count,
          'page': page,
          'per_page': per_page,
          'total_pages': math.ceil(total_count / per_page)
        })
      except Exception as e:
        return jsonify({"error": str(e)}), 500

    # todo POST /study_sessions/:id/review
    @app.route('/api/study-sessions/<id>/review', methods=['POST'])
    @cross_origin()
    def submit_review(id):
      try:
        session_id = id
        data = request.get_json()
        
        if not data:
          return jsonify({"error": "No data provided"}), 400
        
        # Check if the reviews array is provided
        reviews = data.get('reviews', [])
        if not reviews and 'word_id' in data:
          # Handle single review format
          reviews = [data]
        
        if not reviews:
          return jsonify({"error": "No reviews provided"}), 400
        
        cursor = app.db.cursor()
        
        # First check if this session exists
        cursor.execute('SELECT id FROM study_sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        
        if not session:
          return jsonify({"error": f"Study session with ID {session_id} not found"}), 404
        
        # Process each review
        review_ids = []
        for review in reviews:
          word_id = review.get('word_id')
          is_correct = review.get('is_correct', False)
          
          if not word_id:
            continue
          
          # Insert the word review item using session_id
          cursor.execute('''
            INSERT INTO word_review_items (
              session_id,
              word_id,
              is_correct
            )
            VALUES (?, ?, ?)
          ''', (
            session_id, 
            word_id, 
            1 if is_correct else 0  # Convert boolean to int for SQLite
          ))
          
          review_ids.append(cursor.lastrowid)
        
        app.db.commit()
        
        # Return the created reviews
        return jsonify({
          "message": f"Successfully added {len(review_ids)} reviews",
          "review_ids": review_ids
        }), 201
        
      except Exception as e:
        app.db.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500
        
      except Exception as e:
        app.db.rollback()  # Rollback in case of error
        return jsonify({"error": str(e)}), 500

    @app.route('/api/study-sessions/<id>/update-time', methods=['POST'])
    @cross_origin()
    def update_session_time(id):
        try:
            cursor = app.db.cursor()
            
            # Get current timestamp
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Update the session with end_time
            cursor.execute('''
                UPDATE study_sessions
                SET end_time = ?
                WHERE id = ?
            ''', (current_time, id))
            
            app.db.commit()
            
            if cursor.rowcount > 0:
                return jsonify({"message": "Study session time updated successfully"}), 200
            else:
                return jsonify({"error": "Study session not found"}), 404
                
        except Exception as e:
            app.db.rollback()
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/study-sessions/reset', methods=['POST'])
    @cross_origin()
    def reset_study_sessions():
      try:
        cursor = app.db.cursor()
        
        # First delete all word review items since they have foreign key constraints
        cursor.execute('DELETE FROM word_review_items')
        
        # Then delete all study sessions
        cursor.execute('DELETE FROM study_sessions')
        
        app.db.commit()
        
        return jsonify({"message": "Study history cleared successfully"}), 200
      except Exception as e:
        return jsonify({"error": str(e)}), 500
      
