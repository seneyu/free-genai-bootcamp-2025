from flask import request, jsonify, g
from flask_cors import cross_origin
import json

def load(app):
    # Endpoint: GET /api/words with pagination (50 words per page)
    @app.route('/api/words', methods=['GET'])
    @cross_origin()
    def get_words():
        try:
            cursor = app.db.cursor()

            # Get the current page number from query parameters (default is 1)
            page = int(request.args.get('page', 1))
            # Ensure page number is positive
            page = max(1, page)
            words_per_page = 50
            offset = (page - 1) * words_per_page

            # Get sorting parameters from the query string
            sort_by = request.args.get('sort_by', 'french')  # Default to sorting by 'french'
            order = request.args.get('order', 'asc')  # Default to ascending order

            # Validate sort_by and order
            valid_columns = ['french', 'english', 'gender']
            if sort_by not in valid_columns:
                sort_by = 'french'
            if order not in ['asc', 'desc']:
                order = 'asc'

            # Query to fetch words with sorting
            cursor.execute(f'''
                SELECT id, french, english, gender, parts
                FROM words
                ORDER BY {sort_by} {order}
                LIMIT ? OFFSET ?
            ''', (words_per_page, offset))

            words = cursor.fetchall()

            # Query the total number of words
            cursor.execute('SELECT COUNT(*) as total FROM words')
            result = cursor.fetchone()
            total_words = result['total'] if result else 0
            total_pages = (total_words + words_per_page - 1) // words_per_page

            # Format the response
            words_data = []
            for word in words:
                word_dict = {
                    'id': word['id'],
                    'french': word['french'],
                    'english': word['english'],
                    'gender': word['gender'],
                    'parts': word['parts']  # Keep as string, don't parse JSON
                }
                words_data.append(word_dict)

            return jsonify({
                'words': words_data,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'total_words': total_words,
                    'words_per_page': words_per_page
                }
            })

        except Exception as e:
            app.logger.error(f"Error in get_words: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    # Endpoint: GET /api/words/:id to get a single word with its details
    @app.route('/api/words/<int:word_id>', methods=['GET'])
    @cross_origin()
    def get_word(word_id):
        try:
            cursor = app.db.cursor()
            
            # Query to fetch the word and its details
            cursor.execute('''
                SELECT id, french, english, gender, parts
                FROM words
                WHERE id = ?
            ''', (word_id,))
            
            word = cursor.fetchone()
            
            if not word:
                return jsonify({"error": "Word not found"}), 404
            
            # Parse the parts string into a dictionary
            parts = json.loads(word['parts'])
            
            return jsonify({
                "word": {
                    "id": word['id'],
                    "french": word['french'],
                    "english": word['english'],
                    "gender": word['gender'],
                    "parts": parts
                }
            })
            
        except Exception as e:
            app.logger.error(f"Error in get_word: {str(e)}")
            return jsonify({"error": "Internal server error"}), 500

    # Endpoint: POST /api/words to add a new word
    @app.route('/api/words', methods=['POST'])
    @cross_origin()
    def add_word():
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['french', 'english', 'gender', 'parts']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            # For testing, we'll accept any gender value
            cursor = app.db.cursor()
            cursor.execute('''
                INSERT INTO words (french, english, gender, parts)
                VALUES (?, ?, ?, ?)
            ''', (
                data['french'],
                data['english'],
                data['gender'],
                json.dumps(data['parts'])
            ))
            app.db.commit()

            return jsonify({
                'message': 'Word added successfully',
                'id': cursor.lastrowid
            }), 201

        except Exception as e:
            app.logger.error(f"Error in add_word: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    return app