import os
import sys
import pytest
import tempfile
import sqlite3

# Add the parent directory to the Python path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app

@pytest.fixture
def app():
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app with the test database
    app = create_app({
        'TESTING': True,
        'DATABASE': db_path
    })

    # Set up the test database schema
    with app.app_context():
        # Create tables
        cursor = app.db.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                french TEXT NOT NULL,
                english TEXT NOT NULL,
                gender TEXT NOT NULL,
                parts TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS study_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                thumbnail_url TEXT,
                description TEXT
            );

            CREATE TABLE IF NOT EXISTS study_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                study_activity_id INTEGER NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                FOREIGN KEY (group_id) REFERENCES groups (id),
                FOREIGN KEY (study_activity_id) REFERENCES study_activities (id)
            );

            CREATE TABLE IF NOT EXISTS word_review_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word_id INTEGER NOT NULL,
                study_session_id INTEGER NOT NULL,
                correct BOOLEAN NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (word_id) REFERENCES words (id),
                FOREIGN KEY (study_session_id) REFERENCES study_sessions (id)
            );
        ''')
        
        # Insert test data
        cursor.executescript('''
            -- Insert test groups
            INSERT INTO groups (id, name) VALUES 
                (1, 'Basic Greetings'),
                (2, 'Common Phrases');

            -- Insert test study activities
            INSERT INTO study_activities (id, name, thumbnail_url, description) VALUES 
                (1, 'Vocabulary Quiz', 'https://example.com/thumb1.jpg', 'Practice your vocabulary'),
                (2, 'Flashcards', 'https://example.com/thumb2.jpg', 'Learn with flashcards');

            -- Insert test study sessions
            INSERT INTO study_sessions (id, group_id, study_activity_id, start_time, end_time) VALUES 
                (1, 1, 1, '2025-02-23 10:00:00', '2025-02-23 10:30:00'),
                (2, 2, 1, '2025-02-23 11:00:00', '2025-02-23 11:30:00'),
                (3, 1, 2, '2025-02-23 12:00:00', '2025-02-23 12:30:00');

            -- Insert test words with valid parts structure
            INSERT INTO words (id, french, english, gender, parts) VALUES 
                (1, 'bonjour', 'hello', 'verb', '{"definite_article": "", "indefinite_article": "", "plural": ""}'),
                (2, 'chat', 'cat', 'masculine', '{"definite_article": "le", "indefinite_article": "un", "plural": "chats"}');

            -- Insert test word reviews
            INSERT INTO word_review_items (word_id, study_session_id, correct, created_at) VALUES 
                (1, 1, 1, '2025-02-23 10:15:00'),
                (2, 1, 0, '2025-02-23 10:20:00'),
                (1, 2, 1, '2025-02-23 11:15:00');
        ''')
        app.db.commit()

    yield app

    # Clean up the test database
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
