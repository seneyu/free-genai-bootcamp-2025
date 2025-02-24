import sqlite3
import json
from flask import g

class Db:
    def __init__(self, database='words.db'):
        self.database = database

    def get(self):
        if 'db' not in g:
            g.db = sqlite3.connect(self.database)
            # Enable foreign key support
            g.db.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            g.db.row_factory = sqlite3.Row
        return g.db

    def commit(self):
        self.get().commit()

    def cursor(self):
        return self.get().cursor()

    def close(self):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    def sql(self, filepath):
        try:
            with open('sql/' + filepath, 'r') as file:
                return file.read()
        except FileNotFoundError:
            # For testing, return empty string if file doesn't exist
            return ""

    def load_json(self, filepath):
        with open(filepath, 'r') as file:
            return json.load(file)

    def setup_tables(self, cursor):
        try:
            # Create tables if they don't exist
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    french TEXT NOT NULL,
                    english TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    parts TEXT NOT NULL
                );
            ''')
            self.commit()
        except Exception as e:
            print(f"Error setting up tables: {e}")
            raise

    def import_study_activities_json(self, cursor, data_json_path):
        study_activities = self.load_json(data_json_path)
        for activity in study_activities:
            cursor.execute('''
            INSERT INTO study_activities (name, url, preview_url) VALUES (?,?,?)
            ''', (activity['name'], activity['url'], activity['preview_url'],))
        self.get().commit()

    def import_word_json(self, cursor, group_name, data_json_path):
        """Import words from a JSON file into the database"""
        # Create group if it doesn't exist
        cursor.execute('''
            INSERT OR IGNORE INTO groups (name)
            VALUES (?)
        ''', (group_name,))
        
        # Get group id
        cursor.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
        group_id = cursor.fetchone()['id']
        
        # Import words from JSON
        words = self.load_json(data_json_path)
        for word in words:
            # Insert word (use 'none' as default gender for verbs)
            cursor.execute('''
                INSERT INTO words (french, english, gender, parts)
                VALUES (?, ?, ?, ?)
            ''', (word['french'], word['english'], word.get('gender', 'none'), json.dumps(word['parts']),))
            
            # Get word id
            word_id = cursor.lastrowid
            
            # Add word to group
            cursor.execute('''
                INSERT INTO word_groups (word_id, group_id)
                VALUES (?, ?)
            ''', (word_id, group_id))
        self.get().commit()

        # Update the words_count in the groups table by counting all words in the group
        cursor.execute('''
          UPDATE groups
          SET words_count = (
            SELECT COUNT(*) FROM word_groups WHERE group_id = ?
          )
          WHERE id = ?
        ''', (group_id, group_id))

        self.get().commit()

        print(f"Successfully added {len(words)} verbs to the '{group_name}' group.")

    def init(self, app):
        """Initialize the database by running all SQL setup files"""
        cursor = self.cursor()
        
        # Temporarily disable foreign key constraints while dropping tables
        cursor.execute('PRAGMA foreign_keys=OFF')
        
        # Drop all existing tables
        cursor.executescript('''
            DROP TABLE IF EXISTS word_review_items;
            DROP TABLE IF EXISTS word_reviews;
            DROP TABLE IF EXISTS word_groups;
            DROP TABLE IF EXISTS study_sessions;
            DROP TABLE IF EXISTS study_activities;
            DROP TABLE IF EXISTS words;
            DROP TABLE IF EXISTS groups;
        ''')
        
        # Re-enable foreign key constraints
        cursor.execute('PRAGMA foreign_keys=ON')
        
        # Run setup files in order
        setup_files = [
            'setup/create_table_groups.sql',  # Create groups first
            'setup/create_table_words.sql',
            'setup/create_table_word_groups.sql',
        ]
        
        for file in setup_files:
            sql = self.sql(file)
            if sql:
                cursor.executescript(sql)
                print(f"Executed {file}")
        
        # Run migrations in correct order
        migration_files = [
            'migrations/003_update_study_activities.sql',  # This creates study_activities, study_sessions, and word_review_items
        ]
        
        for file in migration_files:
            sql = self.sql(file)
            if sql:
                cursor.executescript(sql)
                print(f"Executed {file}")
        
        # Import seed data
        self.import_word_json(
            cursor=cursor,
            group_name='Core Verbs',
            data_json_path='seed/data_verbs.json'
        )
        
        self.get().commit()

# Create an instance of the Db class
db = Db()
