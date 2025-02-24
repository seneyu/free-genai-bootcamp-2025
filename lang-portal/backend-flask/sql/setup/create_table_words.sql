CREATE TABLE IF NOT EXISTS words (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  french TEXT NOT NULL,
  english TEXT NOT NULL,
  gender TEXT NOT NULL,  -- 'masculine' or 'feminine'
  parts TEXT NOT NULL  -- Store parts as JSON string containing definite_article, indefinite_article, and plural
);