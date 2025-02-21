import streamlit as st
import sys
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.append(root_dir)

# Debug prints to help identify import issues
print("Python path:", sys.path)
print("Root directory:", root_dir)

# Single import attempt with detailed error handling
try:
    print("Attempting to import youtube_transcript_api...")
    from youtube_transcript_api import YouTubeTranscriptApi
    print("Successfully imported YouTubeTranscriptApi")
    
    print("Attempting to import from backend...")
    from backend.get_transcript import YouTubeTranscriptDownloader
    from backend.chat import BedrockChat
    from backend.vector_store import FrenchQuestionVectorStore
    from backend.question_generator import QuestionGenerator
    print("Successfully imported all backend modules")
except ImportError as e:
    print(f"Failed to import: {e}")
    print(f"Python version: {sys.version}")
    import site
    print(f"Site packages: {site.getsitepackages()}")
    st.error(f"Failed to import required modules: {e}")
    sys.exit(1)  # Exit if imports fail to prevent further errors

# Page config
st.set_page_config(
    page_title="French Learning Assistant",
    page_icon="🇫🇷",
    layout="wide"
)

# Initialize all session state variables at the start
def initialize_session_state():
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'bedrock_chat' not in st.session_state:
        st.session_state.bedrock_chat = BedrockChat()
    if 'current_exercise' not in st.session_state:
        st.session_state.current_exercise = None
    if 'answers_submitted' not in st.session_state:
        st.session_state.answers_submitted = False  
    if 'selected_answers' not in st.session_state:
        st.session_state.selected_answers = []

# Initialize session state immediately
initialize_session_state()

def render_header():
    """Render the header section"""
    st.title("🇫🇷 French Learning Assistant")
    st.markdown("""
    Transform YouTube transcripts into interactive French learning experiences.
    
    This tool demonstrates:
    - Base LLM Capabilities
    - RAG (Retrieval Augmented Generation)
    - Amazon Bedrock Integration
    - Agent-based Learning Systems
    """)

def render_sidebar():
    """Render the sidebar with component selection"""
    with st.sidebar:
        st.header("Development Stages")
        
        # Main component selection
        selected_stage = st.radio(
            "Select Stage:",
            [
                "1. Chat with Nova",
                "2. Raw Transcript",
                "3. Structured Data",
                "4. RAG Implementation",
                "5. Interactive Learning"
            ]
        )
        
        # Stage descriptions
        stage_info = {
            "1. Chat with Nova": """
            **Current Focus:**
            - Basic French learning
            - Understanding LLM capabilities
            - Identifying limitations
            """,
            
            "2. Raw Transcript": """
            **Current Focus:**
            - YouTube transcript download
            - Raw text visualization
            - Initial data examination
            """,
            
            "3. Structured Data": """
            **Current Focus:**
            - Text cleaning
            - Dialogue extraction
            - Data structuring
            """,
            
            "4. RAG Implementation": """
            **Current Focus:**
            - Bedrock embeddings
            - Vector storage
            - Context retrieval
            """,
            
            "5. Interactive Learning": """
            **Current Focus:**
            - Scenario generation
            - Audio synthesis
            - Interactive practice
            """
        }
        
        st.markdown("---")
        st.markdown(stage_info[selected_stage])
        
        return selected_stage

def render_chat_stage():
    """Render an improved chat interface"""
    st.header("Chat with Nova")

    # Introduction text
    st.markdown("""
    Start by exploring Nova's base French language capabilities. Try asking questions about French grammar, 
    vocabulary, or cultural aspects.
    """)

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar="🧑‍💻" if message["role"] == "user" else "🤖"):
            st.markdown(message["content"])

    # Chat input area
    if prompt := st.chat_input("Ask about French language..."):
        # Process the user input
        process_message(prompt)

    # Example questions in sidebar
    with st.sidebar:
        st.markdown("### Try These Examples")
        example_questions = [
            "How do I say 'Where is the train station?' in French?",
            "Explain the difference between le and la",
            "What's the polite form of manger?",
            "How do I count objects in French?",
            "What's the difference between bonjour and bonsoir?",
            "How do I ask for directions politely?"
        ]
        
        for q in example_questions:
            if st.button(q, use_container_width=True, type="secondary"):
                # Process the example question
                process_message(q)
                st.rerun()

    # Add a clear chat button
    if st.session_state.messages:
        if st.button("Clear Chat", type="primary"):
            st.session_state.messages = []
            st.rerun()

def process_message(message: str):
    """Process a message and generate a response"""
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": message})
    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(message)

    # Generate and display assistant's response
    with st.chat_message("assistant", avatar="🤖"):
        try:
            response = st.session_state.bedrock_chat.generate_response(message)
            if response:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                st.error("Failed to generate a response. The model returned an empty response.")
        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

def count_characters(text):
    """Count French and total characters in text"""
    if not text:
        return 0, 0
        
    def is_french(char):
        return any([
            '\u0041' <= char <= '\u005a',  # Uppercase letters
            '\u0061' <= char <= '\u007a',  # Lowercase letters
            '\u00c0' <= char <= '\u00d6',  # Uppercase accents
            '\u00d8' <= char <= '\u00f6',  # Lowercase accents
            '\u00f8' <= char <= '\u00ff',  # Other French characters
        ])
    
    fr_chars = sum(1 for char in text if is_french(char))
    return fr_chars, len(text)

def render_transcript_stage():
    """Render the raw transcript stage"""
    st.header("Raw Transcript Processing")
    
    # URL input
    url = st.text_input(
        "YouTube URL",
        placeholder="Enter a French lesson YouTube URL"
    )
    
    # Download button and processing
    if url:
        if st.button("Download Transcript"):
            try:
                downloader = YouTubeTranscriptDownloader()
                transcript = downloader.get_transcript(url)
                if transcript:
                    # Store the raw transcript text in session state
                    transcript_text = "\n".join([entry['text'] for entry in transcript])
                    st.session_state.transcript = transcript_text
                    st.success("Transcript downloaded successfully!")
                else:
                    st.error("No transcript found for this video.")
            except Exception as e:
                st.error(f"Error downloading transcript: {str(e)}")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Raw Transcript")
        if st.session_state.transcript:
            st.text_area(
                label="Raw text",
                value=st.session_state.transcript,
                height=400,
                disabled=True
            )
    
        else:
            st.info("No transcript loaded yet")
    
    with col2:
        st.subheader("Transcript Stats")
        if st.session_state.transcript:
            # Calculate stats
            fr_chars, total_chars = count_characters(st.session_state.transcript)
            total_lines = len(st.session_state.transcript.split('\n'))
            
            # Display stats
            st.metric("Total Characters", total_chars)
            st.metric("French Characters", fr_chars)
            st.metric("Total Lines", total_lines)
        else:
            st.info("Load a transcript to see statistics")

def render_structured_stage():
    """Render the structured data stage"""
    st.header("Structured Data Processing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Dialogue Extraction")
        # Placeholder for dialogue processing
        st.info("Dialogue extraction will be implemented here")
        
    with col2:
        st.subheader("Data Structure")
        # Placeholder for structured data view
        st.info("Structured data view will be implemented here")

def render_rag_stage():
    """Render the RAG implementation stage"""
    st.header("RAG System")
    
    # Query input
    query = st.text_input(
        "Test Query",
        placeholder="Enter a question about French..."
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Retrieved Context")
        # Placeholder for retrieved contexts
        st.info("Retrieved contexts will appear here")
        
    with col2:
        st.subheader("Generated Response")
        # Placeholder for LLM response
        st.info("Generated response will appear here")

def render_interactive_stage():
    """Render the interactive learning stage"""
    st.header("Interactive Learning")
    
    # Initialize question generator
    generator = QuestionGenerator()
    
    # Container for practice type and topic with custom width
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            # Practice type selection with custom width
            practice_type = st.selectbox(
                "Select Practice Type",
                ["Dialogue Practice", "Vocabulary Quiz", "Listening Exercise"],
                key="practice_type"
            )

            # Topic selection below practice type
            topic = st.selectbox(
                "Select Topic",
                list(QuestionGenerator.TOPICS.keys()),
                key="topic"
            )
    
    # Generate button
    if st.button("Generate New Question"):
        with st.spinner("Generating question..."):
            try:
                exercise = generator.generate_practice_question(practice_type, topic)
                if exercise:
                    st.session_state.current_exercise = exercise
                    st.session_state.answers_submitted = False
                    st.session_state.selected_answers = [''] * len(exercise.questions)  # Reset answers
                else:
                    st.error("Failed to generate exercise. Please try again.")
            except Exception as e:
                st.error(f"Error generating question: {str(e)}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Practice Scenario")
        if st.session_state.current_exercise:
            exercise = st.session_state.current_exercise
            st.markdown("### Dialogue")
            st.markdown(exercise.conversation)
            
            st.markdown("### Questions")
            
            # Initialize selected_answers if needed based on current questions length
            if not st.session_state.selected_answers or len(st.session_state.selected_answers) != len(exercise.questions):
                st.session_state.selected_answers = [''] * len(exercise.questions)
            
            current_answers = []
            question_containers = []  # Store containers for feedback
            
            for i, q in enumerate(exercise.questions, 1):
                # Question container
                question_container = st.container()
                question_containers.append(question_container)  # Store for later use
                
                with question_container:
                    st.markdown(f"{i}. {q['question']}")
                    
                    # Create radio options
                    options = [f"{opt}. {text}" for opt, text in zip(['A', 'B', 'C', 'D'], q['options'])]
                    
                    if not st.session_state.answers_submitted:
                        selected = st.radio(
                            f"Question {i}",
                            options,
                            key=f"q_{i}",
                            index=None
                        )
                        if selected:
                            st.session_state.selected_answers[i-1] = selected[0]
                        current_answers.append(st.session_state.selected_answers[i-1])
                    else:
                        # Find the index of the selected answer in options
                        try:
                            selected_index = next((idx for idx, opt in enumerate(options) 
                                            if opt.startswith(st.session_state.selected_answers[i-1])), 0)
                        except Exception:
                            selected_index = 0  # Default to first option if there's an error
                            
                        st.radio(
                            f"Question {i}",
                            options,
                            key=f"q_{i}",
                            index=selected_index,
                            disabled=True
                        )
                
                # Add some space between questions
                st.write("")
            
            # Check if all questions are answered
            answers_complete = all(ans != '' for ans in current_answers)
            
            # Submit button
            if not st.session_state.answers_submitted:
                check_answers = st.button(
                    "Submit Answers",
                    type="primary",
                    disabled=not answers_complete
                )
                
                if not answers_complete:
                    st.warning("Please answer all questions before submitting.")
                
                if check_answers and answers_complete:
                    st.session_state.answers_submitted = True
                    correct_count = 0
                    
                    # Show feedback for each question in their respective containers
                    for i, (container, q, user_answer, correct_answer) in enumerate(zip(
                        question_containers,
                        exercise.questions,
                        st.session_state.selected_answers,
                        exercise.correct_answers
                    ), 1):
                        with container:
                            options = [f"{opt}. {text}" for opt, text in zip(['A', 'B', 'C', 'D'], q['options'])]
                            # Find the appropriate option texts for user and correct answers
                            try:
                                user_option = next((opt for opt in options if opt.startswith(user_answer)), "")
                                correct_option = next((opt for opt in options if opt.startswith(correct_answer)), "")
                                
                                if user_answer == correct_answer:
                                    st.success(f"✅ Correct! {correct_option}")
                                    correct_count += 1
                                else:
                                    st.error(f"❌ Your answer: {user_option}")
                                    st.success(f"Correct answer: {correct_option}")
                            except Exception as e:
                                st.error(f"Error displaying feedback: {str(e)}")
                    
                    # Show celebration for perfect score
                    if correct_count == len(exercise.questions):
                        st.balloons()
                        st.success("Perfect! Excellent work! 🌟")
                    elif correct_count > len(exercise.questions)/2:
                        st.success("Well done! Keep it up! 👍")
                    else:
                        st.info("Keep practicing! You can do it! 💪")
        else:
            st.info("Click 'Generate New Question' to start practicing")
    
    with col2:
        st.subheader("Audio")
        st.info("Audio feature coming soon...")
        
        st.subheader("Conseils d'étude")
        st.info("""
        - Écoutez le dialogue plusieurs fois
        - Notez les mots clés
        - Concentrez-vous sur le contexte
        - Comprenez d'abord le sens général
        """)

def main():
    render_header()
    selected_stage = render_sidebar()
    
    # Render appropriate stage
    if selected_stage == "1. Chat with Nova":
        render_chat_stage()
    elif selected_stage == "2. Raw Transcript":
        render_transcript_stage()
    elif selected_stage == "3. Structured Data":
        render_structured_stage()
    elif selected_stage == "4. RAG Implementation":
        render_rag_stage()
    elif selected_stage == "5. Interactive Learning":
        render_interactive_stage()
    
    # Debug section at the bottom
    with st.expander("Debug Information"):
        st.json({
            "selected_stage": selected_stage,
            "transcript_loaded": st.session_state.transcript is not None,
            "chat_messages": len(st.session_state.messages),
            "session_state_keys": list(st.session_state.keys())  # Show all session state keys
        })

if __name__ == "__main__":
    main()