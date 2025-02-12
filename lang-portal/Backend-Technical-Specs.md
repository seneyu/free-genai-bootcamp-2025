# Backend Server Technical Specs

## Business Goals

We are building a learning portal that acts as launchpad for study activities:

- Have an inventory of words in the target language
- Act as a Learning Record Store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Technical Requirements

- The backend will be built using Python
- The database will be SQLite3
- Invoke is a task runner for Python
- The API will be built using Flask
- The API will always return JSON
- There will be no authentication or authorization

## Directory Structure

```text
backend-flask/
├── app/
│   ├── api/
│   ├── models/
│   └── db/
│       ├── migrations/
│       └── seeds/
├── tests/
└── wsgi.py
```

## Database Schema

Our database will be a single sqlite database called `words.db` that will be in the root of the project folder `backend-flask`.

We have the following tables:

- words - stored vocabulary words
  - id integer
  - french string
  - english string
  - gender string
  - parts json
- words_groups - join table for words and groups many-to-many
  - id integer
  - word_id integer
  - group_id integer
- groups - thematic groups of words
  - id integer
  - name string
- study_sessions - records of study sessions grouping word_review_items
  - id integer
  - group_id integer
  - study_activity_id integer
  - start_time datetime
  - end_time datetime
- study_activities - a specific study activity, linking a study session to group
  - id integer
  - name string
  - thumbnail_url string
  - description string
  - group_id integer
  - created_at datetime
- word_review_items - a record of word practice, determining if the word was correct or not
  - id integer
  - word_id integer
  - study_session_id integer
  - correct boolean
  - created_at datetime

## API Endpoints

### GET /api/dashboard/last_study_session

Returns information about the most recent study session.

#### JSON Response

```json
{
  "study_session": {
    "id": 123,
    "group_id": 456,
    "created_at": "2025-02-08T17:20:23-05:00",
    "study_activity_id": 789,
    "group_name": "Basic Greetings"
  }
}
```

### GET /api/dashboard/study_progress

Returns study progress statistics. Frontend will determine progress bar based on total words studied and total available words.

#### JSON Response

```json
{
  "study_progress": {
    "total_words_studied": 3,
    "total_available_words": 124
  }
}
```

### GET /api/dashboard/quick_stats

Returns quick overview statistics.

#### JSON Response

```json
{
  "success_rate": 80.0,
  "total_study_sessions": 4,
  "total_active_groups": 3,
  "study_streak_days": 4
}
```

### GET /api/study_activities/:id

#### JSON Response

```json
{
  "id": 1,
  "name": "Vocabulary Quiz",
  "thumbnail_url": "https://example.com/thumbnail.jpg",
  "description": "Practice your vocabulary with flashcards"
}
```

### GET /api/study_activities/:id/study_sessions

- pagination with 100 items per page

#### JSON Response

```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 20
  }
}
```

### POST /api/study_activities

#### Request Params:

- group_id integer
- study_activity_id integer

#### JSON Response

```json
{
  "id": 124,
  "group_id": 123
}
```

### GET /api/words

- pagination with 100 items per page

#### JSON Response

```json
{
  "items": [
    {
      "french": "chat",
      "english": "cat",
      "gender": "masculine",
      "parts": {
        "definite_article": "le",
        "indefinite_article": "un",
        "plural": "chats"
      },
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 500,
    "items_per_page": 100
  }
}
```

### GET /api/words/:id

#### JSON Response

```json
{
  "french": "chat",
  "english": "cat",
  "gender": "masculine",
  "parts": {
    "definite_article": "le",
    "indefinite_article": "un",
    "plural": "chats"
  },
  "stats": {
    "correct_count": 5,
    "wrong_count": 2
  },
  "groups": [
    {
      "id": 1,
      "name": "Basic Nouns"
    }
  ]
},
```

### GET /api/groups

- pagination with 100 items per page

#### JSON Response

```json
{
  "items": [
    {
      "id": 1,
      "name": "Basic Nouns",
      "word_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```

### GET /api/groups/:id

#### JSON Response

```json
{
  "id": 1,
  "name": "Basic Nouns",
  "stats": {
    "total_word_count": 20
  }
}
```

### GET /api/groups/:id/words

#### JSON Response

```json
{
  "items": [
    {
      "french": "chat",
      "english": "cat",
      "gender": "masculine",
      "parts": {
        "definite_article": "le",
        "indefinite_article": "un",
        "plural": "chats"
      }
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```

### GET /api/groups/:id/study_sessions

#### JSON Response

```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Nouns",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```

### GET /api/study_sessions

- pagination with 100 items per page

#### JSON Response

```json
{
  "items": [
    {
      "id": 123,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Nouns",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 100
  }
}
```

### GET /api/study_sessions/:id

#### JSON Response

```json
{
  "id": 123,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Nouns",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 20
}
```

### GET /api/study_sessions/:id/words

- pagination with 100 items per page

#### JSON Response

```json
{
  "items": [
    {
      "french": "chat",
      "english": "cat",
      "gender": "masculine",
      "parts": {
        "definite_article": "le",
        "indefinite_article": "un",
        "plural": "chats"
      },
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```

### POST /api/reset_history

#### JSON Response

```json
{
  "success": true,
  "message": "Study history has been reset"
}
```

### POST /api/full_reset

#### JSON Response

```json
{
  "success": true,
  "message": "System has been fully reset"
}
```

### POST /api/study_sessions/:id/words/:word_id/review

#### Request Params

- id (study_session_id) integer
- word_id integer
- correct boolean

#### Request Payload

```json
{
  "correct": true
}
```

#### JSON Response

```json
{
  "success": true,
  "word_id": 1,
  "study_session_id": 123,
  "correct": true,
  "created_at": "2025-02-08T17:33:07-05:00"
}
```

## Tasks Runner Tasks

Invoke is a task runner for Python.
Here is a list of possible tasks we need for our lang portal.

### Initialize Database

This task will initialize the SQLite database `words.db` and set up Flask-Migrate for managing migrations.

```python
from invoke import task

@task
def init_db(ctx):
  """Initialize the database and migrations"""
  # Initialize migrations directory
  ctx.run("flask db init")

  # Create initial migration
  ctx.run("flask db migrate -m 'Initial migration'")

  # Apply migration
  ctx.run("flask db upgrade")
```

### Migrate Database

We will use `Flask-Migrate` to handle database migrations. Migration files will be stored in the `migrations` folder.

Invoke tasks to handle migrations:

```python
from invoke import task

@task
def make_migration(ctx, message):
    """Create a new migration"""
    ctx.run(f"flask db migrate -m '{message}'")

@task
def apply_migration(ctx):
    """Apply pending migrations"""
    ctx.run("flask db upgrade")

@task
def rollback_migration(ctx):
    """Rollback the last migration"""
    ctx.run("flask db downgrade")
```

Example usage:

```bash
# Create a new migration
invoke make-migration --message "Add gender column to words table"

# Apply pending migrations
invoke apply-migration

# Rollback last migration
invoke rollback-migration
```

### Seed Data

This task will import json files and transform them into target data for our database.

All seed files live in the `seeds` folder.
All seed files should be loaded.

In our task we should have a DSL to specify each seed file and its expected group word name.

```json
[
  {
    "french": "voiture",
    "english": "car",
    "gender": "feminine",
    "parts": {
      "definite_article": "la",
      "indefinite_article": "une",
      "plural": "voitures"
    }
  },
  ...
]
```
