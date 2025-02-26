import gradio as gr
import requests
import json
import os
import random
import logging
from PIL import Image
import pytesseract
import io
import traceback
import openai
import dotenv
import re
from difflib import SequenceMatcher

dotenv.load_dotenv()

# Setup Custom Logging -----------------------
logger = logging.getLogger('my_app')
logger.setLevel(logging.DEBUG)

# Create file handler
fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter('%(asctime)s - MY_APP - %(message)s')
fh.setFormatter(formatter)

# Add handler to logger
logger.addHandler(fh)

# Set up console handler as well
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Define global variables
group_names = {"1": "Core Verbs", "2": "Core Nouns", "3": "Core Adjectives"}
vocabulary = []
current_sentence = {}  # Now a dictionary to store both French and English separately
selected_group_id = None
current_word_id = None  # Store the current word ID for review submission
current_session_id = None  # Add this to track the current session
API_BASE_URL = "http://localhost:8000/api"  # Base API URL for backend

# Custom CSS for larger fonts
custom_css = """
body, .gradio-container {
    font-size: 18px !important;
}
.gradio-container button, .gradio-container select, .gradio-container textarea, .gradio-container input {
    font-size: 18px !important;
}
h1 {
    font-size: 32px !important;
}
h2 {
    font-size: 28px !important;
}
h3 {
    font-size: 24px !important;
}
.feedback-box {
    font-size: 20px !important;
    padding: 16px !important;
    border-radius: 8px !important;
    margin-top: 16px !important;
    margin-bottom: 16px !important;
}
label span {
    font-size: 18px !important;
    font-weight: bold !important;
}
.tab-nav button {
    font-size: 22px !important;
}
"""

# Check if tesseract has French language support
has_french_support = False
try:
    pytesseract.image_to_string(Image.new('RGB', (10, 10), color='white'), lang='fra')
    has_french_support = True
except pytesseract.pytesseract.TesseractError as e:
    logger.warning(f"French language support not available: {e}")
    logger.warning("Will use default language for OCR")
except Exception as e:
    logger.warning(f"Error checking tesseract French support: {e}")

def fetch_vocabulary(group_id):
    """Fetch vocabulary from the API"""
    global vocabulary, selected_group_id

    try:
        # Handle different input formats from Gradio dropdown
        if isinstance(group_id, tuple):
            # If it's a tuple (value, label), use the first element (value)
            group_id = group_id[0]
        elif isinstance(group_id, dict) and 'value' in group_id:
            # If it's a dict with 'value' key
            group_id = group_id['value']
        
        # Get group name for display purposes
        group_name = group_names.get(group_id, f"Group {group_id}")
        selected_group_id = group_id
        
        # Log the attempt with improved debugging
        logger.debug(f"Attempting to fetch vocabulary for group ID: {group_id} (Type: {type(group_id)}, Name: {group_name})")
        
        # Use the group_id directly in the URL
        url = f'{API_BASE_URL}/groups/{group_id}/words'
        logger.debug(f"Requesting from URL: {url}")
        
        try:
            response = requests.get(url)
            logger.debug(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    logger.debug(f"Raw API response keys: {response_data.keys() if isinstance(response_data, dict) else 'not a dict'}")
                    
                    # Handle different response formats
                    if isinstance(response_data, dict) and 'words' in response_data:
                        vocabulary = response_data['words']
                    elif isinstance(response_data, list):
                        vocabulary = response_data
                    else:
                        logger.error(f"Unexpected response format: {response_data}")
                        return f"API response format error", display_vocabulary_callback()
                    
                    logger.debug(f"Found {len(vocabulary)} words")
                    
                    # Log the first word to see structure
                    if vocabulary:
                        logger.debug(f"Sample word structure: {vocabulary[0]}")
                    
                    # Ensure each word has the required fields
                    for word in vocabulary:
                        if 'french' not in word or 'english' not in word:
                            logger.warning(f"Word missing required fields: {word}")
                        
                        # Set a default gender if not present
                        if 'gender' not in word and 'parts' in word:
                            # Try to determine gender from parts if available
                            parts = word.get('parts', '').lower()
                            if 'f' in parts:
                                word['gender'] = 'f'
                            else:
                                word['gender'] = 'm'  # Default to masculine
                        elif 'gender' not in word:
                            word['gender'] = 'm'  # Default to masculine
                    
                    logger.debug(f"Received data for group: {group_name}")
                    return f"Successfully loaded {len(vocabulary)} words from {group_name}", display_vocabulary_callback()
                except ValueError as json_err:
                    logger.error(f"Failed to parse JSON: {str(json_err)}")
                    return f"Failed to parse API response: {str(json_err)}", display_vocabulary_callback()
            else:
                error_msg = f"API request failed: {response.status_code}, {response.text}"
                logger.error(error_msg)
                return error_msg, display_vocabulary_callback()
        except requests.exceptions.RequestException as req_err:
            error_msg = f"Network error connecting to API: {str(req_err)}"
            logger.error(error_msg)
            return error_msg, display_vocabulary_callback()
    except Exception as e:
        error_msg = f"Failed to fetch vocabulary: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return error_msg, display_vocabulary_callback()

# Modify the generate_sentence function to work with your API structure
def generate_sentence(word_entry):
    """Generate a sentence using the provided word and return a dictionary with both languages"""
    global current_word_id
    
    logger.debug(f"Generating sentence for word entry: {word_entry}")
    
    # Store the word ID for later review submission
    current_word_id = word_entry.get('id')
    
    # Extract basic word information
    word = word_entry.get('french', '')
    english = word_entry.get('english', '')
    
    # Log the word we're working with
    logger.debug(f"Working with word: {word} ({english}) - ID: {current_word_id}")
    
    # Parse parts if it's a JSON string
    parts_data = {}
    parts_str = word_entry.get('parts', '')
    if parts_str and isinstance(parts_str, str):
        try:
            parts_data = json.loads(parts_str)
            logger.debug(f"Successfully parsed parts data: {parts_data.keys()}")
        except json.JSONDecodeError as e:
            logger.warning(f"Could not parse parts JSON: {e}")
    
    # Determine if it's a verb
    is_verb = False
    
    # Method 1: Check for 'infinitive' in parts_data
    if parts_data and 'infinitive' in parts_data:
        is_verb = True
        logger.debug("Identified as verb from parts data (infinitive field)")
    
    # Method 2: Check word ending
    elif word.endswith(('er', 'ir', 're')):
        is_verb = True
        logger.debug("Identified as verb from word ending")
    
    # Method 3: Check if the English translation begins with "to "
    elif english.lower().startswith('to '):
        is_verb = True
        logger.debug("Identified as verb from English translation")
    
    logger.debug(f"Word type determination: {'Verb' if is_verb else 'Noun/Adjective'}")
    
    # Generate a simple sentence
    if is_verb:
        french_sentence = f"J'aime {word}."
        english_sentence = f"I like to {english.lower().replace('to ', '')}."
    else:
        # Default to masculine
        gender = 'm'
        articles = {"m": "le", "f": "la"}
        article = articles.get(gender, "le")
        
        # If the word starts with a vowel, use l' instead of le/la
        if word[0].lower() in 'aeiouhéèêàâôîïü':
            article = "l'"
        
        french_sentence = f"J'aime {article} {word}."
        english_sentence = f"I like the {english}."
    
    logger.debug(f"Basic sentence generated - French: {french_sentence}, English: {english_sentence}")
    
    # Try to use OpenAI for better sentences if available
    try:
        if "OPENAI_API_KEY" in os.environ:
            logger.debug("Using OpenAI to generate sentence")
            client = openai.OpenAI()
            prompt = f"""
            Generate a compound sentence using this French word: {word} ({english})
            The sentence should be at DELF A2-B1 level French - slightly challenging but still accessible.

            Guidelines:
            - Create a compound sentence with at least two clauses connected by a conjunction (et, mais, ou, car, donc, etc.)
            - Focus on showcasing the provided word in a meaningful context
            - Use appropriate grammar with some variety in tenses (present, past, future)
            - Include a variety of vocabulary related to everyday situations
            - You may include idiomatic expressions if appropriate for this level

            Please provide the sentence in this format:
            French: [compound sentence in French]
            English: [English translation]
            """
            
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI Response: {content}")
            
            # Parse OpenAI response
            french_sentence = ""
            english_sentence = ""
            found_french = False
            found_english = False
            lines = content.split('\n')
            
            for line in lines:
                if line.lower().startswith('french:'):
                    french_sentence = line.replace('French:', '', 1).strip()
                    found_french = True
                elif line.lower().startswith('english:'):
                    english_sentence = line.replace('English:', '', 1).strip()
                    found_english = True

            if not french_sentence or not english_sentence:
                logger.warning("OpenAI response format unexpected, using fallback sentences")
                # Use the fallback sentences from earlier in the function
            else:
                logger.debug(f"Using OpenAI generated - French: {french_sentence}, English: {english_sentence}")
        else:
            logger.debug("OpenAI API key not found, using basic sentence generation")
    except Exception as e:
        logger.error(f"Error using OpenAI: {str(e)}")
        logger.error(traceback.format_exc())
        logger.debug("Using fallback sentence generation due to OpenAI error")
    
    return {
        "french": french_sentence,
        "english": english_sentence
    }

# Update random_sentence_callback to work with the new API structure
def random_sentence_callback():
    """Generate a random sentence using the vocabulary and return only the English part"""
    global vocabulary, current_sentence, current_word_id
    
    try:
        if not vocabulary:
            return "No vocabulary loaded. Please load vocabulary first."
        
        # Log the current state of vocabulary before selecting
        logger.debug(f"Current vocabulary size: {len(vocabulary)}")
        
        # Select a random word and log it
        word_entry = random.choice(vocabulary)
        logger.debug(f"Selected random word entry: {word_entry}")
        
        # Check for required fields
        if 'french' not in word_entry or 'english' not in word_entry:
            logger.error(f"Word entry missing required fields: {word_entry}")
            return "Invalid vocabulary word structure. Please reload vocabulary."
        
        # Log the word being used
        logger.debug(f"Using word for sentence generation: {word_entry['french']} ({word_entry['english']})")
        
        # Generate a sentence using the word entry
        sentence_data = generate_sentence(word_entry)
        
        # Store both French and English
        current_sentence = sentence_data
        
        # Log the generated sentence
        logger.debug(f"Generated French: {sentence_data['french']}")
        logger.debug(f"Generated English: {sentence_data['english']}")
        
        # Return only the English part for display
        return sentence_data["english"]
    except Exception as e:
        error_msg = f"Error generating sentence: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return error_msg

def normalize_french_text(text):
    """Normalize French text for better comparison"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation, except apostrophes in words like j'aime
    text = re.sub(r'[^\w\s\']', '', text)
    
    # Replace multiple spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Trim leading/trailing whitespace
    text = text.strip()
    
    return text

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts using SequenceMatcher"""
    normalized_text1 = normalize_french_text(text1)
    normalized_text2 = normalize_french_text(text2)
    
    # Use SequenceMatcher to get a similarity ratio
    return SequenceMatcher(None, normalized_text1, normalized_text2).ratio()

def determine_grade_and_feedback(transcription, expected_french):
    """Determine the grade and feedback based on OCR transcription and expected French"""
    # If no transcription, there was an OCR error
    if not transcription or transcription.startswith("Error"):
        return "No Grade", "Could not process the image clearly. Please submit a clearer image with better lighting and focus."
    
    # Calculate similarity
    similarity = calculate_similarity(transcription, expected_french)
    logger.debug(f"Similarity score: {similarity}")
    
    # Grade mapping based on similarity
    if similarity >= 0.9:
        grade = "S"
        feedback = "Excellent! Your writing is very accurate."
    elif similarity >= 0.8:
        grade = "A"
        feedback = "Very good! There are minor differences between your answer and the expected French."
    elif similarity >= 0.6:
        grade = "B"
        feedback = "Good attempt. There are some differences to work on."
    elif similarity >= 0.4:
        grade = "C"
        feedback = "Keep practicing. Your answer has several differences from the expected French."
    else:
        grade = "D"
        feedback = "There are significant differences between your answer and the expected French. Keep practicing!"
    
    # Add specific comparison points if needed
    if similarity < 0.9:
        normalized_expected = normalize_french_text(expected_french)
        normalized_transcription = normalize_french_text(transcription)
        
        # Check for common errors
        if "'" in normalized_expected and "'" not in normalized_transcription:
            feedback += " Remember to include apostrophes in contractions like j'aime."
        
        if similarity < 0.6:
            feedback += " Compare your answer with the expected French and try again."
    
    return grade, feedback

def grade_to_score(grade):
    """Convert letter grade to numerical score for API submission"""
    grade_map = {
        "S": 100,
        "A": 90,
        "B": 75,
        "C": 60,
        "D": 40,
        "No Grade": 0,
        "Manual Review": 50
    }
    return grade_map.get(grade, 0)

def perform_ocr(image):
    """Perform OCR with fallback options"""
    try:
        # Convert to grayscale for better OCR
        img = image.convert('L')
        
        # Try OCR with appropriate language settings
        if has_french_support:
            logger.debug("Attempting OCR with French language support")
            transcription = pytesseract.image_to_string(img, lang='fra', config='--psm 6')
        else:
            logger.debug("French language not available, using default language")
            transcription = pytesseract.image_to_string(img, config='--psm 6')
        
        # If empty result, try with different PSM mode
        if not transcription.strip():
            logger.debug("Empty result, trying different PSM mode")
            transcription = pytesseract.image_to_string(img, config='--psm 4')
        
        logger.debug(f"OCR Transcription: {transcription}")
        return transcription.strip()
    except pytesseract.pytesseract.TesseractError as e:
        logger.error(f"Tesseract error: {e}")
        if 'fra.traineddata' in str(e):
            return "French language pack not installed for OCR. Using manual review mode."
        return f"OCR error: {str(e)}"
    except Exception as e:
        logger.error(f"OCR error: {e}")
        logger.error(traceback.format_exc())
        return f"Error in OCR processing: {str(e)}"

def submit_review_to_api(session_id, word_id, grade, transcription, expected_french):
    """Submit word review to the backend API and update session end time"""
    if not session_id or not word_id:
        logger.error("Missing session_id or word_id for API submission")
        return False, "Missing session or word ID"
    
    try:
        # Convert grade to score
        score = grade_to_score(grade)
        is_correct = score >= 70  # Consider S, A, B as correct
        
        # Create payload adjusted to match your frontend API
        payload = {
            "reviews": [{
                "word_id": word_id,
                "is_correct": is_correct
            }]
        }
        
        # Submit to API
        url = f"{API_BASE_URL}/study-sessions/{session_id}/review"
        logger.debug(f"Submitting review to API: {url} with payload: {payload}")
        
        response = requests.post(url, json=payload)
        
        if response.status_code in [200, 201]:
            logger.debug(f"API submission successful: {response.json()}")
            
            # Always update the end_time to the current time
            update_url = f"{API_BASE_URL}/study-sessions/{session_id}/update-time"
            try:
                update_response = requests.post(update_url)
                logger.debug(f"Session time update: {update_response.status_code}")
            except Exception as update_error:
                logger.error(f"Error updating session time: {str(update_error)}")
            
            return True, "Review submitted successfully"
        else:
            logger.error(f"API submission failed: {response.status_code}, {response.text}")
            return False, f"API submission failed: {response.status_code}"
    except Exception as e:
        error_msg = f"Error submitting review to API: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False, error_msg

def create_or_get_study_session():
    """Create a new study session or get the current one"""
    global selected_group_id, current_session_id
    
    if not selected_group_id:
        logger.error("No group selected for creating study session")
        return None, "No vocabulary group selected"
    
    try:
        # Check if we already have an active session for this group
        url = f"{API_BASE_URL}/study-sessions?group_id={selected_group_id}&active=true"
        logger.debug(f"Checking for active session: {url}")
        
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            active_sessions = data.get('study_sessions', [])
            
            if active_sessions:
                # Use the most recent active session
                session_id = active_sessions[0]['id']
                logger.debug(f"Using existing active session: {session_id}")
                current_session_id = session_id  # Store in global
                return session_id, "Using existing session"
                
        # If no active session found or error, create a new one
        create_url = f"{API_BASE_URL}/study-sessions"
        payload = {
            "group_id": selected_group_id,
            "activity_id": 2  # 2 is for Writing Practice
        }
        
        logger.debug(f"Creating new session: {create_url} with payload {payload}")
        create_response = requests.post(create_url, json=payload)
        
        if create_response.status_code == 201:
            session_data = create_response.json()
            session_id = session_data.get('id')
            logger.debug(f"Created new study session: {session_id}")
            current_session_id = session_id  # Store in global
            return session_id, "Created new session"
        else:
            logger.error(f"Failed to create study session: {create_response.status_code}, {create_response.text}")
            return None, f"Failed to create session: {create_response.status_code}"
            
    except Exception as e:
        error_msg = f"Error managing study session: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return None, error_msg

def grade_submission(image):
    """Grade the submitted image with OCR or manual review option and submit to API"""
    global current_sentence, current_word_id
    expected_french = current_sentence.get("french", "")
    
    # Check if image is provided
    if image is None:
        return "No image submitted. Please upload an image.", expected_french, "No Grade", "Please upload a clear image of your handwritten French."
    
    try:
        # Attempt OCR processing
        transcription = perform_ocr(image)
        
        # Special handling for French language pack missing
        if "French language pack not installed" in transcription:
            grade = "Manual Review"
            feedback = "Since OCR can't process French text, please compare your writing with the expected French sentence above."
        # If we couldn't detect any text
        elif not transcription or transcription.startswith("Error"):
            grade = "No Grade"
            feedback = "Please try again with a clearer image. Make sure your handwriting is clearly visible with good lighting."
        else:
            # Determine grade and feedback
            grade, feedback = determine_grade_and_feedback(transcription, expected_french)
        
        # Submit to API if we have a valid word ID
        api_submission_status = ""
        if current_word_id and grade not in ["No Grade"]:
            # Create or get a study session
            session_id, session_msg = create_or_get_study_session()
            
            if session_id:
                success, api_msg = submit_review_to_api(session_id, current_word_id, grade, transcription, expected_french)
                if success:
                    api_submission_status = " (Saved to progress tracker)"
                else:
                    logger.error(f"API submission failed: {api_msg}")
                    api_submission_status = " (Note: Progress not saved)"
            else:
                logger.error(f"No session available: {session_msg}")
                api_submission_status = " (Note: Progress not saved)"
                
        # Add API submission status to feedback
        feedback += api_submission_status
        
        return transcription or "OCR couldn't detect text clearly.", expected_french, grade, feedback
        
    except Exception as e:
        logger.error(f"Error in grade_submission: {e}")
        logger.error(traceback.format_exc())
        return f"Error processing submission: {str(e)}", expected_french, "No Grade", "An error occurred. Please try again with a clearer image."

# Update display_vocabulary_callback to match the API structure
def display_vocabulary_callback():
    """Create a formatted display of vocabulary"""
    global vocabulary
    
    if not vocabulary:
        return "No vocabulary loaded."
    
    display_text = "**Vocabulary List**\n\n"
    display_text += "| French | English | Type |\n"
    display_text += "|--------|---------|------|\n"
    
    for word in vocabulary:
        french = word.get('french', '')
        english = word.get('english', '')
        
        # Determine word type
        word_type = "Unknown"
        parts_str = word.get('parts', '')
        if parts_str and isinstance(parts_str, str):
            try:
                parts_data = json.loads(parts_str)
                if 'infinitive' in parts_data:
                    word_type = "Verb"
                else:
                    word_type = "Noun/Adjective"
            except json.JSONDecodeError:
                pass
        elif french.endswith(('er', 'ir', 're')):
            word_type = "Verb"
            
        display_text += f"| {french} | {english} | {word_type} |\n"
    
    return display_text

def create_grade_display(grade, feedback):
    """Create HTML for grade display with color coding"""
    color_map = {
        "S": "#4CAF50",  # Green
        "A": "#8BC34A",  # Light Green
        "B": "#FFEB3B",  # Yellow
        "C": "#FF9800",  # Orange
        "D": "#F44336",  # Red
        "No Grade": "#9E9E9E",  # Gray
        "Manual Review": "#2196F3"  # Blue
    }
    
    color = color_map.get(grade, "#9E9E9E")
    text_color = "#FFFFFF" if grade not in ["B", "No Grade"] else "#000000"
    
    return f"""
    <div style="background-color:{color}; color:{text_color}; padding:16px; border-radius:8px; margin-top:16px;">
        <h3 style="margin:0; font-size:24px;">Grade: {grade}</h3>
        <p style="margin-top:8px; font-size:20px;">{feedback}</p>
    </div>
    """

def create_demo():
    """Create the Gradio interface"""
    global current_session_id
    
    with gr.Blocks(title="French Learning App", css=custom_css) as demo:
        gr.HTML("""
        <style>
        .gradio-container {
            font-size: 18px !important;
        }
        </style>
        """)
        
        gr.Markdown("# French Writing Practice", elem_id="title")
        
        # Create a hidden component to store session ID for JavaScript
        session_id_store = gr.Textbox(visible=False, value="")
        
        with gr.Tab("Setup"):
            with gr.Row():
                with gr.Column():
                    # Group selection dropdown - Use a simple list with specific format
                    group_dropdown = gr.Dropdown(
                        choices=["1", "2", "3"],  # Just use the IDs
                        label="Select Vocabulary Group",
                        value="1",
                        elem_classes="large-text"
                    )
                    load_button = gr.Button("Load Vocabulary", size="lg")
                    load_result = gr.Textbox(label="Result", elem_classes="large-text")
                
                with gr.Column():
                    vocabulary_display = gr.Markdown("No vocabulary loaded.", elem_classes="large-text")
            
            # Load vocabulary button click event
            load_button.click(
                fn=lambda group_id: fetch_vocabulary(group_id),
                inputs=[group_dropdown],
                outputs=[load_result, vocabulary_display],
                api_name="load_vocabulary"
            )
            
            # Button to view vocabulary
            view_vocab_button = gr.Button("View Vocabulary", size="lg")
            view_vocab_button.click(
                fn=display_vocabulary_callback,
                inputs=[],
                outputs=[vocabulary_display],
                api_name="view_vocabulary"
            )
        
        with gr.Tab("Practice"):
            with gr.Row():
                with gr.Column():
                    generate_button = gr.Button("Generate Random Sentence", size="lg")
                    sentence_display = gr.Textbox(
                        label="Translate this sentence to French", 
                        lines=4,
                        elem_classes="large-text"
                    )
                
                with gr.Column():
                    gr.Markdown("### Instructions:", elem_id="instructions-title")
                    gr.Markdown("1. Generate a random sentence", elem_classes="large-text")
                    gr.Markdown("2. Write the French translation on paper", elem_classes="large-text")
                    gr.Markdown("3. Take a photo or screenshot of your writing", elem_classes="large-text")
                    gr.Markdown("4. Upload the image for review", elem_classes="large-text")
            
            # Generate sentence button click event
            generate_button.click(
                fn=random_sentence_callback,
                inputs=[],
                outputs=[sentence_display],
                api_name="generate_sentence"
            )
            
            # Upload image for grading
            with gr.Row():
                with gr.Column():
                    image_input = gr.Image(
                        type="pil", 
                        label="Upload your written answer",
                        elem_classes="large-text"
                    )
                    submit_button = gr.Button("Submit for Review", size="lg")
                
                with gr.Column():
                    transcription_output = gr.Textbox(
                        label="OCR Transcription", 
                        lines=2,
                        elem_classes="large-text"
                    )
                    expected_french_output = gr.Textbox(
                        label="Expected French", 
                        lines=2,
                        elem_classes="large-text"
                    )
                    grade_output = gr.Textbox(
                        label="Grade",
                        elem_classes="large-text"
                    )
                    feedback_output = gr.Textbox(
                        label="Feedback", 
                        lines=3,
                        elem_classes="large-text"
                    )
                    
                    # Add HTML component for styled grade display
                    grade_html = gr.HTML(
                        """<div style="background-color:#f0f0f0; padding:16px; border-radius:8px;">
                        <h3>Grade: Not yet graded</h3>
                        <p>Submit your writing for review</p>
                        </div>"""
                    )
            
            # Helper function to update session ID and then grade submission
            def session_aware_grade_submission(image):
                # This will update session_id_store with the current session ID
                result = grade_submission(image)
                if current_session_id:
                    # Update the session ID store for JavaScript
                    return result[0], result[1], result[2], result[3], str(current_session_id)
                return result[0], result[1], result[2], result[3], ""
            
            # Submit button click event with proper outputs
            submit_button.click(
                fn=session_aware_grade_submission,
                inputs=[image_input],
                outputs=[
                    transcription_output, 
                    expected_french_output,
                    grade_output,
                    feedback_output,
                    session_id_store
                ],
                api_name="grade_submission"
            )
            
            # Add a separate event for updating the HTML display
            submit_button.click(
                fn=lambda img: create_grade_display(*determine_grade_and_feedback(perform_ocr(img), current_sentence.get("french", ""))),
                inputs=[image_input],
                outputs=[grade_html]
            )
        
        # Add JavaScript for auto-saving
        demo.load(
            None,
            js="""
            function setupAutoSave() {
                // Get the session ID from the hidden component
                const sessionIdElement = document.querySelector("input[data-testid='textbox']");
                if (sessionIdElement && sessionIdElement.value) {
                    window._current_session_id = sessionIdElement.value;
                    console.log("Session ID set:", window._current_session_id);
                }
                
                // Function to update session time
                function updateSessionTime() {
                    if (window._current_session_id) {
                        const apiUrl = "http://localhost:8000/api/study-sessions/" + 
                                      window._current_session_id + "/update-time";
                        
                        fetch(apiUrl, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            }
                        })
                        .then(response => {
                            console.log('Session time updated:', response.status);
                        })
                        .catch(error => {
                            console.error('Error updating session time:', error);
                        });
                    }
                }
                
                // Update time every 30 seconds
                setInterval(updateSessionTime, 30000);
                
                // Also update when the page is about to be closed
                window.addEventListener('beforeunload', function() {
                    if (window._current_session_id) {
                        updateSessionTime();
                    }
                });
            }
            
            // Run setup once the page is loaded
            if (document.readyState === 'complete') {
                setupAutoSave();
            } else {
                window.addEventListener('load', setupAutoSave);
            }
            """
        )
        
    return demo

# Create and launch the app
if __name__ == "__main__":
    logger.info("Starting French Learning App with Gradio")
    
    # Check and log Tesseract status
    try:
        version = pytesseract.get_tesseract_version()
        logger.info(f"Tesseract version: {version}")
        if has_french_support:
            logger.info("French language support is available")
        else:
            logger.warning("French language support is NOT available")
    except Exception as e:
        logger.warning(f"Could not verify Tesseract installation: {e}")
    
    app = create_demo()
    app.launch(server_port=8081)