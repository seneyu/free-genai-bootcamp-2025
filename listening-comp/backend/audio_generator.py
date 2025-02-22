import json
from pathlib import Path
from typing import List, Dict
import boto3
from .chat import BedrockChat
import subprocess
import tempfile
import os
from botocore.exceptions import BotoCoreError, ClientError
import logging
from datetime import datetime
import shutil

class AudioGenerator:
    def __init__(self):
        # Configure logging
        logging.basicConfig(level=logging.INFO, 
                           format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        try:
            self.chat = BedrockChat()
            self.polly = boto3.client('polly')
            self.polly.describe_voices(LanguageCode='fr-FR')
        except (BotoCoreError, ClientError) as e:
            logging.error(f"AWS Configuration Error: {str(e)}")
            raise Exception(
                "Failed to initialize AWS Polly. Please ensure AWS credentials are configured correctly. "
                "You need to either:\n"
                "1. Run 'aws configure' if you have AWS CLI installed\n"
                "2. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables\n"
                "3. Create credentials file in ~/.aws/credentials"
            )

        # Check if ffmpeg is installed
        self._check_ffmpeg()

        # Create directories with full path
        self.base_dir = Path(__file__).parent / "data"
        self.audio_dir = self.base_dir / "audio"
        self.temp_dir = self.base_dir / "temp"

        # Ensure all directories exist with proper permissions
        for directory in [self.base_dir, self.audio_dir, self.temp_dir]:
            os.makedirs(directory, exist_ok=True)
            # Ensure write permissions
            os.chmod(directory, 0o755)

        logging.info(f"Directories created: base={self.base_dir}, audio={self.audio_dir}, temp={self.temp_dir}")
        
        # Define French voices for different genders - IMPORTANT: Use exact names from AWS Polly
        self.voices = {
            "male": ["Mathieu", "Remi"],  # French male voices
            "female": ["Lea", "Celine"],  # French female voices (note: no accent on Lea)
            "neutral": ["Mathieu"]  # Default fallback
        }
        
        # Shorter pauses (in milliseconds)
        self.pause_durations = {
            'short': 1000,    # 1 second (between lines)
            'medium': 1500,   # 1.5 seconds (after intro)
            'long': 2000      # 2 seconds (before questions)
        }
        
        # Verify the voices exist in Polly
        self._verify_voices()
    
    def _verify_voices(self):
        """Verify that the configured voices exist in Amazon Polly"""
        try:
            response = self.polly.describe_voices(LanguageCode='fr-FR')
            available_voices = [voice['Id'] for voice in response['Voices']]
            
            logging.info(f"Available French voices: {available_voices}")
            
            # Check each configured voice
            for gender, voices in self.voices.items():
                for i, voice in enumerate(voices):
                    if voice not in available_voices:
                        logging.warning(f"Voice '{voice}' for {gender} not found in Polly. Removing it.")
                        self.voices[gender].pop(i)
            
            # Ensure we have at least one voice for each gender
            for gender in self.voices:
                if not self.voices[gender]:
                    # If no voices for this gender, use a default
                    if 'Mathieu' in available_voices:
                        self.voices[gender] = ['Mathieu']
                    else:
                        # Use the first available French voice
                        self.voices[gender] = [available_voices[0]]
            
            logging.info(f"Final voice configuration: {self.voices}")
            
        except Exception as e:
            logging.error(f"Error verifying voices: {e}")
            # Set fallback voices
            self.voices = {
                "male": ["Mathieu"],
                "female": ["Celine"],
                "neutral": ["Mathieu"]
            }
    
    def _check_ffmpeg(self):
        """Verify that ffmpeg is installed and accessible"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
            if result.returncode != 0:
                raise Exception("ffmpeg is not working properly")
            logging.info("ffmpeg is available")
        except FileNotFoundError:
            logging.error("ffmpeg is not installed or not in PATH")
            raise Exception(
                "ffmpeg is required but not found. Please install ffmpeg:\n"
                "- On macOS: brew install ffmpeg\n"
                "- On Ubuntu/Debian: sudo apt-get install ffmpeg\n"
                "- On Windows: Download from https://ffmpeg.org/download.html"
            )
    
    def format_dialogue_for_audio(self, conversation: str, questions: List[Dict]) -> Dict:
        """Format dialogue with speaker annotations and use the provided questions"""
        # Prepare questions text for the prompt
        questions_text = ""
        for i, q in enumerate(questions, 1):
            questions_text += f"{i}. {q['question']}\n"
            for j, option in enumerate(q['options']):
                option_letter = chr(65 + j)  # A, B, C, D
                questions_text += f"   {option_letter}) {option}\n"
            questions_text += "\n"

        prompt = f"""You are an assistant helping to format dialogues for audio generation.

Here is a French dialogue:
{conversation}

And here are the comprehension questions that go with this dialogue:
{questions_text}

Your task:
1. Add a brief narrator's introduction in French (e.g., "Écoutez le dialogue suivant...")
2. Identify the speakers and their gender from the dialogue
3. Structure the dialogue with clear speaking turns

Respond only with a JSON in this format:
{{
    "intro": "French introduction by narrator",
    "speakers": [
        {{"name": "Name1", "gender": "male/female"}},
        {{"name": "Name2", "gender": "male/female"}}
    ],
    "dialogue": [
        {{"speaker": "Narrator", "text": "French introduction..."}},
        {{"speaker": "Name1", "text": "French dialogue line..."}},
        {{"speaker": "Name2", "text": "French response..."}},
    ],
    "questions": [
        {{"speaker": "Narrator", "text": "1. {questions[0]['question']}"}},
        {{"speaker": "Narrator", "text": "A) {questions[0]['options'][0]}"}},
        {{"speaker": "Narrator", "text": "B) {questions[0]['options'][1]}"}},
        {{"speaker": "Narrator", "text": "C) {questions[0]['options'][2]}"}},
        {{"speaker": "Narrator", "text": "D) {questions[0]['options'][3]}"}},
        {{"speaker": "Narrator", "text": "2. {questions[1]['question'] if len(questions) > 1 else ''}"}},
        {{"speaker": "Narrator", "text": "A) {questions[1]['options'][0] if len(questions) > 1 else ''}"}},
        {{"speaker": "Narrator", "text": "B) {questions[1]['options'][1] if len(questions) > 1 else ''}"}},
        {{"speaker": "Narrator", "text": "C) {questions[1]['options'][2] if len(questions) > 1 else ''}"}},
        {{"speaker": "Narrator", "text": "D) {questions[1]['options'][3] if len(questions) > 1 else ''}"}},
    ]
}}

Important:
- Keep all dialogue text in French
- Make sure the introduction is appropriate for a language learning context
- Use natural French speech patterns and expressions
- Don't include the introductory text again in the dialogue lines - avoid repetition
- The questions section MUST use EXACTLY the questions and options provided above
"""

        try:
            response = self.chat.generate_response(prompt)
            formatted = json.loads(response)
            
            # Validate the response structure
            required_keys = ["intro", "speakers", "dialogue", "questions"]
            if not all(key in formatted for key in required_keys):
                raise ValueError("Missing required sections in formatted dialogue")
            
            # Remove any dialogue entries from Narrator that might duplicate the intro
            if formatted["dialogue"] and formatted["dialogue"][0]["speaker"] == "Narrator":
                intro_text = formatted["intro"].lower()
                first_line = formatted["dialogue"][0]["text"].lower()
                
                if (intro_text in first_line or first_line in intro_text or
                    "dialogue" in first_line or "conversation" in first_line):
                    formatted["dialogue"] = formatted["dialogue"][1:]
            
            # Verify the questions match the provided questions
            # If they don't, we'll regenerate them directly from the provided questions
            has_correct_questions = True
            if len(formatted["questions"]) < len(questions) * 5:  # Each question + 4 options
                has_correct_questions = False
                
            # If questions don't match, rebuild them manually
            if not has_correct_questions:
                formatted["questions"] = []
                for i, q in enumerate(questions, 1):
                    formatted["questions"].append({"speaker": "Narrator", "text": f"{i}. {q['question']}"})
                    for j, option in enumerate(q['options']):
                        option_letter = chr(65 + j)  # A, B, C, D
                        formatted["questions"].append({"speaker": "Narrator", "text": f"{option_letter}) {option}"})
            
            return formatted
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse response as JSON: {str(e)}")
            # Create a fallback format with the original questions
            fallback = {
                "intro": "Écoutez le dialogue suivant.",
                "speakers": [
                    {"name": "Speaker1", "gender": "male"},
                    {"name": "Speaker2", "gender": "female"}
                ],
                "dialogue": []
            }
            
            # Extract lines from the conversation
            lines = conversation.strip().split('\n')
            current_speaker = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Try to identify speaker lines (assuming format like "Name: Text")
                speaker_match = re.match(r"^([^:]+):\s*(.+)$", line)
                if speaker_match:
                    speaker_name = speaker_match.group(1).strip()
                    text = speaker_match.group(2).strip()
                    fallback["dialogue"].append({
                        "speaker": speaker_name, 
                        "text": text
                    })
                else:
                    # If no speaker identified, alternate between speakers
                    if not current_speaker or current_speaker == "Speaker2":
                        current_speaker = "Speaker1"
                    else:
                        current_speaker = "Speaker2"
                    fallback["dialogue"].append({
                        "speaker": current_speaker,
                        "text": line
                    })
            
            # Add questions
            fallback["questions"] = []
            for i, q in enumerate(questions, 1):
                fallback["questions"].append({"speaker": "Narrator", "text": f"{i}. {q['question']}"})
                for j, option in enumerate(q['options']):
                    option_letter = chr(65 + j)  # A, B, C, D
                    fallback["questions"].append({"speaker": "Narrator", "text": f"{option_letter}) {option}"})
            
            return fallback
        except Exception as e:
            logging.error(f"Error formatting dialogue: {str(e)}")
            raise
    
    def get_voice_for_speaker(self, speaker_name: str, speaker_gender: str, speakers_list: List[Dict]) -> str:
        """Get appropriate voice based on speaker and gender"""
        if speaker_name.lower() == "narrator":
            return self.voices["neutral"][0]  # Use neutral voice for narrator
            
        # Try to find the speaker in the speakers list
        for speaker in speakers_list:
            if speaker["name"] == speaker_name:
                gender = speaker["gender"].lower()
                if gender in self.voices and self.voices[gender]:
                    return self.voices[gender][0]
        
        # If we can't find the speaker or their gender isn't specified, use the provided gender
        if speaker_gender.lower() in self.voices and self.voices[speaker_gender.lower()]:
            return self.voices[speaker_gender.lower()][0]
            
        # Fallback to neutral voice
        return self.voices["neutral"][0]
    
    def generate_audio_segment(self, text: str, voice_id: str) -> str:
        """Generate audio segment using Amazon Polly"""
        try:
            logging.info(f"Generating audio with voice: {voice_id}")
            response = self.polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                LanguageCode='fr-FR'
            )
            
            # Create unique temporary file for this segment
            temp_path = os.path.join(self.temp_dir, f"segment_{hash(text) & 0xFFFFFFFF}.mp3")
            
            if "AudioStream" in response:
                with open(temp_path, 'wb') as temp_file:
                    temp_file.write(response["AudioStream"].read())
                    
                # Verify the file exists and has content
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
                    return temp_path
                else:
                    raise Exception(f"Generated empty audio file: {temp_path}")
            else:
                raise Exception("No AudioStream in Polly response")
        except Exception as e:
            logging.error(f"Error generating audio segment: {e}")
            raise
    
    def combine_audio_files(self, audio_files: List[str], output_file: str):
        """Combine multiple audio files using ffmpeg with full decoding/encoding"""
        try:
            # Create file list for ffmpeg
            file_list_path = os.path.join(self.temp_dir, f"filelist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(file_list_path, 'w') as f:
                for audio_file in audio_files:
                    if os.path.exists(audio_file):
                        f.write(f"file '{audio_file}'\n")
                    else:
                        logging.warning(f"File not found: {audio_file}")
            
            # Combine files with full decoding/encoding (not using copy)
            result = subprocess.run([
                'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
                '-i', file_list_path,
                '-ar', '44100',  # Explicitly set audio sample rate
                '-ac', '1',      # Mono audio channel
                '-c:a', 'libmp3lame',  # Force MP3 encoding
                '-b:a', '128k',   # Set bitrate
                output_file
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg error: {result.stderr}")
                
            # Verify file was created properly
            if not os.path.exists(output_file) or os.path.getsize(output_file) < 1000:
                raise Exception(f"Output file missing or too small: {output_file}")
                
            # Cleanup temporary files
            os.unlink(file_list_path)
            
        except Exception as e:
            logging.error(f"Error combining audio files: {e}")
            raise
    
    def generate_silence(self, duration_ms: int) -> str:
        """Generate a silence file using ffmpeg"""
        try:
            # Create a unique filename for this silence duration
            silence_file = os.path.join(self.temp_dir, f"silence_{duration_ms}_{datetime.now().strftime('%H%M%S')}.mp3")
            
            # Generate silence file
            result = subprocess.run([
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', f'anullsrc=r=44100:cl=mono',
                '-t', f'{duration_ms/1000}',
                '-c:a', 'libmp3lame',
                '-b:a', '128k',
                silence_file
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logging.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg error: {result.stderr}")
            
            if not os.path.exists(silence_file) or os.path.getsize(silence_file) < 100:
                raise Exception(f"Failed to create valid silence file at {silence_file}")
                
            return silence_file
            
        except Exception as e:
            logging.error(f"Error generating silence file: {e}")
            raise
    
    def generate_exercise_audio(self, conversation: str, questions: List[Dict]) -> str:
        """Generate full audio for an exercise"""
        # Generate unique filename based on timestamp and content hash
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_hash = str(hash(conversation + str(questions)))[:8]
        filename = f"exercise_{timestamp}_{content_hash}.mp3"
        output_file = os.path.join(self.audio_dir, filename)
        
        if os.path.exists(output_file):
            return output_file
        
        audio_segments = []
        temp_files_to_cleanup = []
        
        try:
            # Format dialogue for audio generation - pass in the actual questions
            audio_format = self.format_dialogue_for_audio(conversation, questions)
            
            logging.info("Generating audio segments...")
            
            # Intro with pause (always use narrator voice)
            intro_audio = self.generate_audio_segment(audio_format["intro"], self.voices["neutral"][0])
            audio_segments.append(intro_audio)
            temp_files_to_cleanup.append(intro_audio)
            
            # Add silence after intro (medium pause)
            silence_medium = self.generate_silence(self.pause_durations['medium'])
            audio_segments.append(silence_medium)
            temp_files_to_cleanup.append(silence_medium)
            
            # Dialogue with pauses between turns - using appropriate voices for each speaker
            for i, line in enumerate(audio_format["dialogue"]):
                speaker = line["speaker"]
                text = line["text"]
                
                # Find the appropriate voice based on speaker
                speaker_gender = "neutral"
                for s in audio_format["speakers"]:
                    if s["name"] == speaker:
                        speaker_gender = s["gender"].lower()
                        break
                
                # Get voice ID for this speaker
                voice_id = self.get_voice_for_speaker(speaker, speaker_gender, audio_format["speakers"])
                
                logging.info(f"Processing dialogue line {i+1}/{len(audio_format['dialogue'])} - Speaker: {speaker}, Gender: {speaker_gender}, Voice: {voice_id}")
                
                # Generate audio for this line with the appropriate voice
                segment = self.generate_audio_segment(text, voice_id)
                audio_segments.append(segment)
                temp_files_to_cleanup.append(segment)
                
                # Add silence between lines (short pause)
                silence_short = self.generate_silence(self.pause_durations['short'])
                audio_segments.append(silence_short)
                temp_files_to_cleanup.append(silence_short)
            
            # Extra pause before questions (long pause)
            silence_long = self.generate_silence(self.pause_durations['long'])
            audio_segments.append(silence_long)
            temp_files_to_cleanup.append(silence_long)
            
            # Process questions in groups (each question followed by its options)
            q_index = 0
            while q_index < len(audio_format["questions"]):
                # Process the question
                question_text = audio_format["questions"][q_index]["text"]
                segment = self.generate_audio_segment(question_text, self.voices["neutral"][0])
                audio_segments.append(segment)
                temp_files_to_cleanup.append(segment)
                
                # Add a short pause after the question
                silence_short = self.generate_silence(self.pause_durations['short'])
                audio_segments.append(silence_short)
                temp_files_to_cleanup.append(silence_short)
                
                # Process the options (next 4 items)
                options_end = min(q_index + 5, len(audio_format["questions"]))
                for opt_index in range(q_index + 1, options_end):
                    option_text = audio_format["questions"][opt_index]["text"]
                    option_segment = self.generate_audio_segment(option_text, self.voices["neutral"][0])
                    audio_segments.append(option_segment)
                    temp_files_to_cleanup.append(option_segment)
                    
                    # Brief pause after each option
                    silence_very_short = self.generate_silence(500)  # 0.5 second
                    audio_segments.append(silence_very_short)
                    temp_files_to_cleanup.append(silence_very_short)
                
                # Add a medium pause after each complete question with options
                silence_medium = self.generate_silence(self.pause_durations['medium'])
                audio_segments.append(silence_medium)
                temp_files_to_cleanup.append(silence_medium)
                
                # Move to the next question (skip the 4 options we just processed)
                q_index = options_end
            
            # Verify all audio segments exist
            valid_segments = []
            for segment in audio_segments:
                if os.path.exists(segment) and os.path.getsize(segment) > 0:
                    valid_segments.append(segment)
                else:
                    logging.warning(f"Missing or empty audio segment: {segment}")
            
            logging.info(f"Combining {len(valid_segments)} audio segments...")
            
            # Combine all segments
            self.combine_audio_files(valid_segments, output_file)
            logging.info(f"Created final audio file: {output_file}")
            
            # Verify output file
            if os.path.exists(output_file) and os.path.getsize(output_file) > 10000:
                logging.info(f"Successfully created audio file: {output_file} ({os.path.getsize(output_file)} bytes)")
            else:
                logging.error(f"Output file problem: {output_file} - Size: {os.path.getsize(output_file) if os.path.exists(output_file) else 'file missing'}")
            
            # Clean up temp files
            self.cleanup_specific_files(temp_files_to_cleanup)
            
            return output_file
            
        except Exception as e:
            logging.error(f"Error generating exercise audio: {e}")
            # Clean up any temp files on error
            self.cleanup_specific_files(temp_files_to_cleanup)
            raise
    
    def cleanup_specific_files(self, files_list):
        """Clean up specific temporary files"""
        for file in files_list:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                logging.warning(f"Error cleaning up temp file {file}: {e}")
                
    def cleanup_temp_files(self):
        """Clean up all temporary files"""
        try:
            for file in os.listdir(self.temp_dir):
                if file.endswith('.mp3') or file.endswith('.txt'):
                    os.remove(os.path.join(self.temp_dir, file))
        except Exception as e:
            logging.warning(f"Error cleaning up temp files: {e}")