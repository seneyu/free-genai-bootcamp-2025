-- Create groups table
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create study_activities table
CREATE TABLE IF NOT EXISTS study_activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create study_sessions table
CREATE TABLE IF NOT EXISTS study_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER NOT NULL,
    activity_id INTEGER NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (activity_id) REFERENCES study_activities(id)
);

-- Create word_review_items table
CREATE TABLE IF NOT EXISTS word_review_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    is_correct BOOLEAN NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES study_sessions(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
);

-- Create group_words table for many-to-many relationship
CREATE TABLE IF NOT EXISTS group_words (
    group_id INTEGER NOT NULL,
    word_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, word_id),
    FOREIGN KEY (group_id) REFERENCES groups(id),
    FOREIGN KEY (word_id) REFERENCES words(id)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_study_sessions_group ON study_sessions(group_id);
CREATE INDEX IF NOT EXISTS idx_study_sessions_activity ON study_sessions(activity_id);
CREATE INDEX IF NOT EXISTS idx_word_review_items_session ON word_review_items(session_id);
CREATE INDEX IF NOT EXISTS idx_word_review_items_word ON word_review_items(word_id);
CREATE INDEX IF NOT EXISTS idx_group_words_group ON group_words(group_id);
CREATE INDEX IF NOT EXISTS idx_group_words_word ON group_words(word_id);
