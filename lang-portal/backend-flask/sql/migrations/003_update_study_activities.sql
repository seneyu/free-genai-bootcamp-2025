-- First drop dependent tables
DROP TABLE IF EXISTS word_review_items;
DROP TABLE IF EXISTS study_sessions;
DROP TABLE IF EXISTS study_activities;

-- Recreate study_activities table with all columns
CREATE TABLE study_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    preview_url TEXT,
    thumbnail_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Recreate study_sessions table
CREATE TABLE study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (activity_id) REFERENCES study_activities(id)
);

-- Recreate word_review_items table
CREATE TABLE word_review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    is_correct BOOLEAN NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
);

-- Insert default study activities
INSERT INTO study_activities (name, description, url, preview_url, thumbnail_url) VALUES 
-- ('Flashcards', 'Practice vocabulary with flashcards', '/study/flashcards', '/images/flashcards-preview.jpg', '/images/flashcards-thumb.jpg'),
-- ('Multiple Choice', 'Test your knowledge with multiple choice questions', '/study/multiple-choice', '/images/quiz-preview.jpg', '/images/quiz-thumb.jpg'),
('Typing Tutor', 'Practice typing Frech words', 'http://localhost:8080', '/assets/study_activities/typing-tutor.png', '/assets/study_activities/typing-tutor.png'),
('Writing Practice', 'Practice writing French sentences', 'http://localhost:8081', '/images/writing-preview.jpg', '/images/writing-thumb.jpg');

-- Recreate indexes
CREATE INDEX IF NOT EXISTS idx_study_sessions_group ON study_sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_activity ON study_sessions(activity_id);
CREATE INDEX IF NOT EXISTS idx_word_review_items_session ON word_review_items(session_id);
CREATE INDEX IF NOT EXISTS idx_word_review_items_word ON word_review_items(word_id);
