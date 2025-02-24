CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  french TEXT NOT NULL,
  english TEXT NOT NULL,
  gender TEXT NOT NULL,  -- 'masculine', 'feminine', 'verb', or 'adjective'
  parts TEXT NOT NULL  -- Store parts as JSON string
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_words_french ON words(french);
CREATE INDEX IF NOT EXISTS idx_words_english ON words(english);
CREATE INDEX IF NOT EXISTS idx_words_gender ON words(gender);