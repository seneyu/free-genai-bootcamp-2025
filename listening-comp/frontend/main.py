import sys
import os
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from backend.question_generator import QuestionGenerator
from backend.question_store import QuestionStore
from datetime import datetime
from backend.audio_generator import AudioGenerator

# Page config
st.set_page_config(
    page_title="French Learning Assistant",
    page_icon="🇫🇷",
    layout="wide"
)

# Initialize session state variables
if 'current_exercise' not in st.session_state:
    st.session_state.current_exercise = None
if 'answers_submitted' not in st.session_state:
    st.session_state.answers_submitted = False
if 'selected_answers' not in st.session_state:
    st.session_state.selected_answers = []

def main():
    st.title("🇫🇷 French Learning Assistant")
    
    # Initialize generators and stores
    generator = QuestionGenerator()
    question_store = QuestionStore()
    audio_generator = AudioGenerator()
    
    # Sidebar for saved questions
    with st.sidebar:
        st.header("Saved Questions")
        saved_questions = question_store.load_all_questions()
        
        if saved_questions:
            selected_question = st.selectbox(
                "Select a saved question",
                options=saved_questions,
                format_func=lambda x: f"{x['topic']} - {datetime.fromisoformat(x['timestamp']).strftime('%Y-%m-%d %H:%M')} ({x['practice_type']})",
                key="saved_question"
            )
            
            if st.button("Load Selected Question"):
                # Convert stored question to exercise format
                exercise = type('Exercise', (), {
                    'conversation': selected_question['conversation'],
                    'questions': selected_question['questions'],
                    'correct_answers': selected_question['correct_answers']
                })()
                
                # Reset all session state variables
                st.session_state.current_exercise = exercise
                st.session_state.answers_submitted = False
                st.session_state.selected_answers = [''] * len(exercise.questions)
                
                # Clear radio button selections by regenerating their keys
                for i in range(len(exercise.questions)):
                    if f"q_{i}" in st.session_state:
                        del st.session_state[f"q_{i}"]
                
                st.rerun()
        else:
            st.info("No saved questions yet.")
    
    # Main content
    # Container for practice type and topic
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            practice_type = st.selectbox(
                "Select Practice Type",
                ["Dialogue Practice", "Vocabulary Quiz", "Listening Exercise"],
                key="practice_type"
            )

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
                    # Save the generated question
                    question_store.save_question(topic, practice_type, exercise)
                    
                    # Reset all session state variables
                    st.session_state.current_exercise = exercise
                    st.session_state.answers_submitted = False
                    st.session_state.selected_answers = [''] * len(exercise.questions)
                    
                    # Clear radio button selections
                    for i in range(len(exercise.questions)):
                        if f"q_{i}" in st.session_state:
                            del st.session_state[f"q_{i}"]
                    
                    st.rerun()
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
            
            if not st.session_state.selected_answers or len(st.session_state.selected_answers) != len(exercise.questions):
                st.session_state.selected_answers = [''] * len(exercise.questions)
            
            current_answers = []
            question_containers = []
            
            for i, q in enumerate(exercise.questions, 1):
                question_container = st.container()
                question_containers.append(question_container)
                
                with question_container:
                    st.markdown(f"{i}. {q['question']}")
                    
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
                        try:
                            selected_index = next((idx for idx, opt in enumerate(options) 
                                            if opt.startswith(st.session_state.selected_answers[i-1])), 0)
                        except Exception:
                            selected_index = 0
                            
                        st.radio(
                            f"Question {i}",
                            options,
                            key=f"q_{i}",
                            index=selected_index,
                            disabled=True
                        )
                
                st.write("")
            
            answers_complete = all(ans != '' for ans in current_answers)
            
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
                    
                    for i, (container, q, user_answer, correct_answer) in enumerate(zip(
                        question_containers,
                        exercise.questions,
                        st.session_state.selected_answers,
                        exercise.correct_answers
                    ), 1):
                        with container:
                            options = [f"{opt}. {text}" for opt, text in zip(['A', 'B', 'C', 'D'], q['options'])]
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
        if st.session_state.current_exercise:
            exercise = st.session_state.current_exercise
            
            # Generate audio button
            if "audio_file" not in st.session_state:
                st.session_state.audio_file = None
                
            if st.button("Generate Audio"):
                with st.spinner("Generating audio..."):
                    try:
                        # Clear previous audio if exists
                        if "audio_bytes" in st.session_state:
                            del st.session_state.audio_bytes
                            
                        # Generate new audio file
                        audio_file = audio_generator.generate_exercise_audio(
                            exercise.conversation,
                            exercise.questions
                        )
                        
                        # Verify file exists and has content
                        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
                            st.session_state.audio_file = audio_file
                            
                            # Read file immediately to cache the bytes
                            with open(audio_file, "rb") as f:
                                st.session_state.audio_bytes = f.read()
                                
                            st.success(f"Audio generated successfully: {os.path.basename(audio_file)} ({os.path.getsize(audio_file)/1024:.1f} KB)")
                        else:
                            st.error(f"Audio file was not created properly: {audio_file}")
                    except Exception as e:
                        st.error(f"Error generating audio: {str(e)}")
                        import traceback
                        st.exception(traceback.format_exc())
            
            # Audio playback
            if "audio_bytes" in st.session_state and st.session_state.audio_bytes:
                st.audio(st.session_state.audio_bytes, format="audio/mp3")
                
                # Provide download option
                if st.session_state.audio_file:
                    filename = os.path.basename(st.session_state.audio_file)
                    st.download_button(
                        label="Download Audio",
                        data=st.session_state.audio_bytes,
                        file_name=filename,
                        mime="audio/mp3"
                    )
            elif st.session_state.audio_file and os.path.exists(st.session_state.audio_file):
                try:
                    # Try reading the file again if bytes weren't cached
                    with open(st.session_state.audio_file, "rb") as f:
                        audio_bytes = f.read()
                    st.audio(audio_bytes, format="audio/mp3")
                    st.session_state.audio_bytes = audio_bytes  # Cache for next time
                except Exception as e:
                    st.error(f"Error reading audio file: {str(e)}")
        else:
            st.info("Audio feature will be available after generating a question")

if __name__ == "__main__":
    main()