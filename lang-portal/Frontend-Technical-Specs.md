# Frontend Technical Specs

## Pages

### Dashboard `/dashboard`

#### Purpose

This page is to provide a summary of learning and act as the default page when a user visits the web app.

#### Components

This page contains the following components:

- Last Study Session
  - Shows last activity used
  - Shows when last activity used
  - Summarizes correct vs wrong from last activity
  - Has a link to the group
- Study Progress
  - Total words study
    - Across all study session show the total words studied out of all possible words in our database
  - Display a mastery progress eg. 0%
- Quick Stats
  - Success rate eg. 80%
  - Total study sessions eg. 4
  - Total active groups eg. 3
  - Study streak eg. 4 days
- Start Studying Button
  - Goes to study activities page

#### Needed API Endpoints

- GET /api/dashboard/last_study_session
- GET /api/dashboard/study_progress
- GET /api/dashboard/quick-stats

### Study Activities Index `/study_acitivities`

This page is to show a collection of study activities with a thumbnail and its name, to either launch or view the study activity.

#### Components

- Study Activity Card
  - Shows a thumbnail and the name of the study activity
  - A launch button to take us to the launch page
  - A view page to view more information about past study sessions for this study activity

#### Needed API Endpoints

- GET /api/study_activities

### Study Activity Show `/study_activities/:id`

#### Purpose

This page is to show the details of a study activity and its past study sessions.

#### Components

- A thumbnail and the name of the study activity
- A description of the study activity
- A launch button to take us to the launch page
- Study activities paginated list
  - Columns
    - Id
    - Activity Name
    - Group Name
    - Start Time
    - End Time (inferred by the last word_review_item submitted)
    - Number of review items

#### Needed API Endpoints

- GET /api/study_activities/:id
- GET /api/study_activities/:id/study_sessions

### Study Activities Launch `/study_activities/:id/launch`

#### Purpose

This page is to launch a study activity.

#### Components

- Name of the study activity
- Launch form
  - select field for group
  - launch npw button

#### Needed API Endpoints

- POST /api/study_activities

After the form is submitted, a new tab opens with the study activity based on its URL provided in the database. The page will then redirect to the study session show page.

### Words Index `/words`

#### Purpose

This page is to show all words in our database.

#### Components

- Paginated word list
  - Columns
    - French
    - English
    - Correct Count
    - Wrong Count
  - Pagination with 100 items per page
  - Clicking the French word will take us to the word show page

#### Needed API Endpoints

- GET /api/words

### Word Show `/words/:id`

#### Purpose

This page is to show information about a specific word.

#### Components

- French
- English
- Gender
- Study Statistics
  - Correct Count
  - Wrong Count
- Word Groups
  - Show a series of pill eg. tags
  - When group name is clicked, it will take us to the group show page

#### Needed API Endpoints

- GET /api/words/:id

### Word Groups Index `/groups`

#### Purpose

This page is to show a list of groups in our database.

#### Components

- Paginated Group List
  - Columns
    - Group Name
    - Word Count
  - Clicking the group name will take us to the group show page

#### Needed API Endpoints

- GET /api/groups

### Group Show `/groups/:id`

#### Purpose

This page is to show information about a specific group.

#### Components

- Group Name
- Group Statistics
  - Total Word Count
- Words in Group (paginated list of words)
  - Should use the same component as the words index page
- Study Sessions (paginated list of study sessions)
  - Should use the same component as the study sessions index page

#### Needed API Endpoints

- GET /api/groups/:id (the name and groups stats)
- GET /api/groups/:id/words
- GET /api/groups/:id/study_sessions

### Study Sessions Index `/study_sessions`

#### Purpose

This page is to show a list of study sessions in our database.

#### Components

- Paginated Study Session List
  - Columns
    - Id
    - Acitivity Name
    - Group Name
    - Start Time
    - End Time
    - Number of Review Items
  - Clicking the study session id will take us to the study session show page

#### Needed API Endpoints

- GET /api/study_sessions

### Study Sessions Show `/study_sessions/:id`

#### Purpose

This page is to show information about a specific study session.

#### Components

- Study Session Details
  - Activity Name
  - Group Name
  - Start Time
  - End Time
  - Number of Review Items
- Words Review Items (paginated list of words)
  - Should use the same component as the words index page

#### Needed API Endpoints

- GET /api/study_sessions/:id
- GET /api/study_sessions/:id/words

### Settings Page `/settings`

#### Purpose

This page is to make configurations to the study portal.

#### Components

- Theme Selection eg. Light, Dark, System Default
- Reset History Button
  - This will delete all study sessions and word review
- Full Reset Button
  - This will drop all tables and re-create with seed data

#### Needed API Endpoints

- POST /api/reset_history
- POST /api/full_reset
