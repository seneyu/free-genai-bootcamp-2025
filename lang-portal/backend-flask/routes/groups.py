from flask import request, jsonify, g
from flask_cors import cross_origin
import json

def load(app):
  @app.route('/api/groups', methods=['GET'])
  @cross_origin()
  def get_groups():
    try:
      print("Starting get_groups function")
      cursor = app.db.cursor()

      # Get the current page number from query parameters (default is 1)
      page = int(request.args.get('page', 1))
      groups_per_page = 10
      offset = (page - 1) * groups_per_page

      # Get sorting parameters from the query string
      sort_by = request.args.get('sort_by', 'name')  # Default to sorting by 'name'
      order = request.args.get('order', 'asc')  # Default to ascending order

      # Validate sort_by and order
      valid_columns = ['name', 'words_count']
      if sort_by not in valid_columns:
        sort_by = 'name'
      if order not in ['asc', 'desc']:
        order = 'asc'

      print(f"Query params: page={page}, sort_by={sort_by}, order={order}")

      # Query to fetch groups with sorting and the word count
      query = f'''
        SELECT 
          g.id, 
          g.name, 
          COALESCE(g.description, '') as description,
          (SELECT COUNT(*) FROM word_groups wg WHERE wg.group_id = g.id) as words_count
        FROM groups g
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
      '''
      print(f"Executing query: {query}")
      
      # First check if groups table exists
      cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='groups'")
      table_exists = cursor.fetchone()
      print(f"Groups table exists: {table_exists is not None}")

      if not table_exists:
        return jsonify({"error": "Groups table does not exist"}), 500

      # Check groups table schema
      cursor.execute("PRAGMA table_info(groups)")
      columns = cursor.fetchall()
      print(f"Groups table columns: {columns}")

      cursor.execute(query, (groups_per_page, offset))
      groups = cursor.fetchall()
      print(f"Found {len(groups)} groups")

      if len(groups) > 0:
        print(f"First group data: {dict(groups[0])}")

      # Query the total number of groups
      cursor.execute('SELECT COUNT(*) FROM groups')
      total_groups = cursor.fetchone()[0]
      total_pages = (total_groups + groups_per_page - 1) // groups_per_page
      print(f"Total groups: {total_groups}, Total pages: {total_pages}")

      # Format the response
      groups_data = []
      for group in groups:
        groups_data.append({
          "id": group["id"],
          "group_name": group["name"],
          "description": group["description"],
          "word_count": group["words_count"]
        })

      response = {
        'groups': groups_data,
        'total_pages': total_pages,
        'current_page': page
      }
      print(f"Returning response: {response}")
      return jsonify(response)
    except Exception as e:
      print(f"Error in get_groups: {str(e)}")
      print(f"Error type: {type(e)}")
      import traceback
      traceback.print_exc()
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:id>', methods=['GET'])
  @cross_origin()
  def get_group(id):
    try:
      cursor = app.db.cursor()

      # Get group details
      cursor.execute('''
        SELECT id, name, words_count
        FROM groups
        WHERE id = ?
      ''', (id,))
      
      group = cursor.fetchone()
      if not group:
        return jsonify({"error": "Group not found"}), 404

      return jsonify({
        "id": group["id"],
        "group_name": group["name"],
        "word_count": group["words_count"]
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  @app.route('/api/groups/<int:id>/words', methods=['GET'])
  @cross_origin()
  def get_group_words(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = int(request.args.get('page', 1))
      words_per_page = 10
      offset = (page - 1) * words_per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'french')
      order = request.args.get('order', 'asc')

      # Validate sort parameters
      valid_columns = ['french', 'english', 'parts', 'correct_count', 'wrong_count']
      if sort_by not in valid_columns:
        sort_by = 'french'
      if order not in ['asc', 'desc']:
        order = 'asc'

      # First, check if the group exists
      cursor.execute('SELECT name FROM groups WHERE id = ?', (id,))
      group = cursor.fetchone()
      if not group:
        return jsonify({"error": "Group not found"}), 404

      # Query to fetch words with pagination and sorting
      cursor.execute(f'''
        SELECT w.*, 
               COALESCE(wr.correct_count, 0) as correct_count,
               COALESCE(wr.wrong_count, 0) as wrong_count
        FROM words w
        JOIN word_groups wg ON w.id = wg.word_id
        LEFT JOIN word_reviews wr ON w.id = wr.word_id
        WHERE wg.group_id = ?
        ORDER BY {sort_by} {order}
        LIMIT ? OFFSET ?
      ''', (id, words_per_page, offset))
      
      words = cursor.fetchall()

      # Get total words count for pagination
      cursor.execute('''
        SELECT COUNT(*) 
        FROM word_groups 
        WHERE group_id = ?
      ''', (id,))
      total_words = cursor.fetchone()[0]
      total_pages = (total_words + words_per_page - 1) // words_per_page

      # Format the response
      words_data = []
      for word in words:
        words_data.append({
          "id": word["id"],
          "french": word["french"],
          "english": word["english"],
          "parts": word["parts"],
          "correct_count": word["correct_count"],
          "wrong_count": word["wrong_count"]
        })

      return jsonify({
        'words': words_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500

  # todo GET /groups/:id/words/raw

  @app.route('/api/groups/<int:id>/study_sessions', methods=['GET'])
  @cross_origin()
  def get_group_study_sessions(id):
    try:
      cursor = app.db.cursor()
      
      # Get pagination parameters
      page = int(request.args.get('page', 1))
      sessions_per_page = 10
      offset = (page - 1) * sessions_per_page

      # Get sorting parameters
      sort_by = request.args.get('sort_by', 'created_at')
      order = request.args.get('order', 'desc')  # Default to newest first

      # Map frontend sort keys to database columns
      sort_mapping = {
        'startTime': 'created_at',
        'endTime': 'last_activity_time',
        'activityName': 'a.name',
        'groupName': 'g.name',
        'reviewItemsCount': 'review_count'
      }

      # Use mapped sort column or default to created_at
      sort_column = sort_mapping.get(sort_by, 'created_at')

      # Get total count for pagination
      cursor.execute('''
        SELECT COUNT(*)
        FROM study_sessions
        WHERE group_id = ?
      ''', (id,))
      total_sessions = cursor.fetchone()[0]
      total_pages = (total_sessions + sessions_per_page - 1) // sessions_per_page

      # Get study sessions for this group with dynamic calculations
      cursor.execute(f'''
        SELECT 
          s.id,
          s.group_id,
          s.study_activity_id,
          s.created_at as start_time,
          (
            SELECT MAX(created_at)
            FROM word_review_items
            WHERE study_session_id = s.id
          ) as last_activity_time,
          a.name as activity_name,
          g.name as group_name,
          (
            SELECT COUNT(*)
            FROM word_review_items
            WHERE study_session_id = s.id
          ) as review_count
        FROM study_sessions s
        JOIN study_activities a ON s.study_activity_id = a.id
        JOIN groups g ON s.group_id = g.id
        WHERE s.group_id = ?
        ORDER BY {sort_column} {order}
        LIMIT ? OFFSET ?
      ''', (id, sessions_per_page, offset))
      
      sessions = cursor.fetchall()
      sessions_data = []
      
      for session in sessions:
        # If there's no last_activity_time, use start_time + 30 minutes
        end_time = session["last_activity_time"]
        if not end_time:
            end_time = cursor.execute('SELECT datetime(?, "+30 minutes")', (session["start_time"],)).fetchone()[0]
        
        sessions_data.append({
          "id": session["id"],
          "group_id": session["group_id"],
          "group_name": session["group_name"],
          "study_activity_id": session["study_activity_id"],
          "activity_name": session["activity_name"],
          "start_time": session["start_time"],
          "end_time": end_time,
          "review_items_count": session["review_count"]
        })

      return jsonify({
        'study_sessions': sessions_data,
        'total_pages': total_pages,
        'current_page': page
      })
    except Exception as e:
      return jsonify({"error": str(e)}), 500