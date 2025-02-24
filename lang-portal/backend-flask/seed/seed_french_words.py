import sqlite3
import json
import os

def seed_french_words():
    # Connect to the database
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'words.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing data
        cursor.execute('DELETE FROM words')
        
        # Load verbs
        with open('seed/data_verbs.json', 'r', encoding='utf-8') as f:
            verbs = json.load(f)
            for verb in verbs:
                cursor.execute('''
                    INSERT INTO words (french, english, gender, parts)
                    VALUES (?, ?, ?, ?)
                ''', (
                    verb['french'],
                    verb['english'],
                    'verb',  # Use 'verb' as gender for verbs
                    json.dumps(verb['parts'])
                ))

        # Load adjectives
        with open('seed/data_adjectives.json', 'r', encoding='utf-8') as f:
            adjectives = json.load(f)
            for adj in adjectives:
                cursor.execute('''
                    INSERT INTO words (french, english, gender, parts)
                    VALUES (?, ?, ?, ?)
                ''', (
                    adj['french'],
                    adj['english'],
                    'adjective',  # Use 'adjective' as gender for adjectives
                    json.dumps(adj['parts'])
                ))

        conn.commit()
        print("Successfully seeded French words into database!")
        
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def assign_words_to_groups():
    """Assign words to appropriate groups"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'words.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Clear existing group assignments
        cursor.execute('DELETE FROM group_words')

        # Get group IDs
        cursor.execute('SELECT id, name FROM groups')
        groups = {row[1]: row[0] for row in cursor.fetchall()}

        # Get basic verbs (être, avoir, aller, faire)
        cursor.execute('''
            INSERT INTO group_words (group_id, word_id)
            SELECT ?, id FROM words 
            WHERE french IN ('être', 'avoir', 'aller', 'faire', 'aimer', 'manger', 'boire', 'dormir')
            OR (gender = 'adjective' AND french IN ('petit', 'grand', 'beau', 'bon', 'chaud', 'froid'))
        ''', (groups['Beginner Vocabulary'],))

        # Get common expressions (more complex verbs)
        cursor.execute('''
            INSERT INTO group_words (group_id, word_id)
            SELECT ?, id FROM words 
            WHERE french IN ('pouvoir', 'vouloir', 'devoir', 'savoir', 'dire', 'voir', 'prendre', 'parler')
            OR (gender = 'adjective' AND french IN ('heureux', 'triste', 'rapide', 'lent', 'facile', 'difficile'))
        ''', (groups['Common Phrases'],))

        # Get advanced words (complex verbs and adjectives)
        cursor.execute('''
            INSERT INTO group_words (group_id, word_id)
            SELECT ?, id FROM words 
            WHERE french IN ('croire', 'comprendre', 'connaître', 'préférer', 'répondre', 'suivre', 'vivre')
            OR (gender = 'adjective' AND french IN ('intelligent', 'courageux', 'prudent', 'sage', 'riche', 'pauvre'))
        ''', (groups['Advanced Words'],))

        conn.commit()
        print("Successfully assigned words to groups!")
        
    except Exception as e:
        print(f"Error assigning words to groups: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    seed_french_words()
    assign_words_to_groups()