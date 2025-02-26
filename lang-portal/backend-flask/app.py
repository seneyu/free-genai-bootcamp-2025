from flask import Flask, g
from flask_cors import CORS
import json
from datetime import datetime, timedelta
import os

from lib.db import Db

import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities



def init_db(app):
    """Initialize database and create tables"""
    try:
        cursor = app.db.cursor()
        
        # Execute all migration files in order
        migration_dir = os.path.join(os.path.dirname(__file__), 'sql', 'migrations')
        migration_files = sorted([f for f in os.listdir(migration_dir) if f.endswith('.sql')])
        
        migrations = [
            'sql/migrations/001_create_words_table.sql',
            'sql/migrations/002_create_study_tables.sql',
            'sql/migrations/003_update_study_activities.sql'
        ]

        for migration in migrations:
            with open(migration, 'r') as f:
                cursor.executescript(f.read())

        app.db.commit()
        app.logger.info("Database initialized successfully")
    except Exception as e:
        app.logger.error(f"Error initializing database: {str(e)}")
        app.db.rollback()
        raise e

def seed_database(app):
    """Seed the database with sample data"""
    try:
        cursor = app.db.cursor()
        
        # Insert sample study activities if none exist
        cursor.execute('SELECT COUNT(*) as count FROM study_activities')
        if cursor.fetchone()['count'] == 0:
            cursor.executescript('''
                INSERT INTO study_activities (name, description) VALUES
                    ('Flashcards', 'Review words using flashcards'),
                    ('Quiz', 'Test your knowledge with a quiz'),
                    ('Writing', 'Practice writing sentences');
            ''')
        
        # Insert sample groups if none exist
        cursor.execute('SELECT COUNT(*) as count FROM groups')
        if cursor.fetchone()['count'] == 0:
            cursor.executescript('''
                INSERT INTO groups (name, description) VALUES
                    ('Core Verbs', 'Essential French verbs for everyday communication'),
                    ('Common Phrases', 'Everyday French expressions and greetings'),
                    ('Advanced Words', 'Advanced vocabulary for fluent conversations');
            ''')
            
            # Add words to groups
            cursor.execute('SELECT id FROM groups WHERE name = ?', ('Core Verbs',))
            core_verbs_group = cursor.fetchone()
            if core_verbs_group:
                cursor.execute('SELECT id FROM words')
                words = cursor.fetchall()
                for word in words:
                    cursor.execute('''
                        INSERT INTO word_groups (group_id, word_id)
                        VALUES (?, ?)
                    ''', (core_verbs_group['id'], word['id']))

        # Insert sample study sessions if none exist
        cursor.execute('SELECT COUNT(*) as count FROM study_sessions')
        if cursor.fetchone()['count'] == 0:
            # Get a group ID and activity ID
            cursor.execute('SELECT id FROM groups LIMIT 1')
            group = cursor.fetchone()
            cursor.execute('SELECT id FROM study_activities LIMIT 1')
            activity = cursor.fetchone()
            
            if group and activity:
                # Create some study sessions
                now = datetime.now()
                cursor.execute('''
                    INSERT INTO study_sessions (group_id, activity_id, start_time, end_time)
                    VALUES (?, ?, ?, ?)
                ''', (group['id'], activity['id'], now - timedelta(days=1), now - timedelta(days=1, minutes=30)))
                
                # Get the session ID
                session_id = cursor.lastrowid
                
                # Add some word reviews
                cursor.execute('SELECT id FROM words LIMIT 5')
                words = cursor.fetchall()
                for word in words:
                    cursor.execute('''
                        INSERT INTO word_review_items (session_id, word_id, is_correct)
                        VALUES (?, ?, ?)
                    ''', (session_id, word['id'], True))

        app.db.commit()
    except Exception as e:
        app.logger.error(f"Error seeding database: {str(e)}")
        app.db.rollback()

def get_allowed_origins(app):
    try:
        cursor = app.db.cursor()
        cursor.execute('SELECT url FROM study_activities')
        urls = cursor.fetchall()
        # Convert URLs to origins (e.g., https://example.com/app -> https://example.com)
        origins = set()
        for url in urls:
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url['url'])
                origin = f"{parsed.scheme}://{parsed.netloc}"
                origins.add(origin)
            except:
                continue
        return list(origins) if origins else ["*"]
    except:
        return ["*"]  # Fallback to allow all origins if there's an error

def create_app(test_config=None):
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_mapping(
            DATABASE='words.db'
        )
    else:
        app.config.update(test_config)
    
    # Initialize database
    app.db = Db(database=app.config['DATABASE'])
    
    # Ensure database is initialized within app context
    with app.app_context():
        init_db(app)
        seed_database(app)
    
    # Get allowed origins from study_activities table
    allowed_origins = get_allowed_origins(app)
    
    # In development, add localhost to allowed origins
    if app.debug:
        allowed_origins.extend(["http://localhost:8080", "http://127.0.0.1:8080"])
    
    # Configure CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Register routes
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    routes.dashboard.load(app)
    routes.study_activities.load(app)

    from error_handler import register_error_handlers, setup_api_logging
    register_error_handlers(app)
    setup_api_logging(app)
    
    # Register database close function
    @app.teardown_appcontext
    def close_db(error):
        app.db.close()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='localhost', port=8000, debug=True)