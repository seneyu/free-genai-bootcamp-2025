# Tech Specs

## Business Goal

Create a program that will find lyrics off the internet for a target song in a specific language and produce vocabulary to be imported into our database.

## Technical Requirements

- FastAPI
- Ollama via the Ollama Python SDK
  - Mistral 7B
- Instructor (for structured json output)
- SQLite3 (for database)
- duckduckgo-search (to search for lyrics)

## API Endpoints

### GetLyrics POST /api/agent

### Behavior

This endpoint goes to our agent which uses the reAct framework so that it can go to the internet, find multiple possible version of lyrics and then extract out the correct lyrics and format the lyrics into vocabulary.

Tools available:

- tools/extract_vocabulary.py
- tools/get_page_content.py
- tools/search_web.py

### Request Parameters

- `message_request` (str): A string that describes the song and/or artist to get lyrics for a song from the internet

### JSON Response

- `lyrics` (str): The lyrics of the song
- `vocabulary` (list): A list of vocabulary words found in the lyrics
