import sqlite3
import json

def check_database():
    conn = sqlite3.connect('word_bank.db')
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM words')
    total = cursor.fetchone()[0]
    print(f"\nTotal words in database: {total}")
    
    # Show sample of each type
    for word_type in ['verb', 'adjective']:
        print(f"\nSample {word_type}s:")
        cursor.execute('SELECT french, english, gender, parts FROM words WHERE gender = ? LIMIT 3', (word_type,))
        for row in cursor.fetchall():
            french, english, gender, parts = row
            parts_dict = json.loads(parts)
            print(f"\nFrench: {french}")
            print(f"English: {english}")
            print(f"Gender: {gender}")
            print(f"Parts: {json.dumps(parts_dict, indent=2)}")
    
    conn.close()

if __name__ == '__main__':
    check_database()
