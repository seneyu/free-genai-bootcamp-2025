# Technical Specs

## Initialization

When the app first initializes it needs the following:

- Fetch from the GET localhost:8000/api/groups/{group_id}/words, this will return a collection of words in a json structure. It will have French words with their English translation. We need to store this collection of words in memory.

## Page State

The Page State describes the state of the single page application should behave from a user's perspective.

### Setup

When the user first start up the app, they will only see a button called "Generate Sentence". When they press the button, the app will generate a sentence using the Sentence Generator LLM, and the state will move to Practice State.

## Practice State

When the user is in practice state, they will see an English sentence, an upload field under the English sentence, and a button called "Submit for Review". When they press the "Submit for Review" button, an uploaded image will be passed to the Grading System and then will transition to the Review State.

## Review State

When the user is in the Review State, the user will still see the English sentence. The upload field will be gone. The user will now see a review of the output from the Grading System:

- Transcription of the image
- Translation of the transcription
- Grading

  - a letter score using the S Rank to score
  - a description of whether the attempt was accurate to the English sentencce and suggestions

There will be a button called "Next Question", which clicked, it will generate a new question and transition the app into Practice State.

## Sentence Generator LLM Prompt

Generate a sentence using the following word: {{word}}
The grammar should be scoped to DELF A2-B1 level French.

## Grading System

The Grading System will do the following:

- transcribe the image using Tesseract OCR
- use an LLM to produce a literal translation of the transcription
- use another LLM to produce a grade
- return the data to the frontend app
