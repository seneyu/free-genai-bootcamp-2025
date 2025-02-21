from typing import Optional, Dict, List, Tuple
import boto3
import os
import re
import glob
import argparse
import textwrap

MODEL_ID = "amazon.nova-lite-v1:0"

class FrenchTranscriptStructurer:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Bedrock client"""
        self.bedrock_client = boto3.client('bedrock-runtime', region_name="us-east-1")
        self.model_id = model_id

    def split_transcript_into_sections(self, text: str) -> List[str]:
        """
        Split a plain text transcript into separate conversational sections.
        Uses patterns like multiple line breaks or typical dialog markers.
        """
        # Clean up whitespace first
        text = re.sub(r'\s+', ' ', text)
        
        # Try to identify dialog boundaries
        # Look for common French dialog markers or speaker changes
        dialog_markers = [
            r'(?:bonjour|salut|allô|merci|au revoir|à bientôt|monsieur|madame|mesdames|messieurs)',
            r'(?:s\'il vous plaît|pardon|excusez-moi)',
            r'(?:je vous|nous vous|je t\'|je te|tu peux|vous pouvez)'
        ]
        
        # Create a pattern that looks for these markers
        pattern = '|'.join(dialog_markers)
        
        # Split the text based on these markers
        # Keep the markers with the text that follows them
        splits = []
        last_pos = 0
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if match.start() > last_pos + 20:  # Ensure sections have some minimal length
                splits.append(text[last_pos:match.start()].strip())
                last_pos = match.start()
        
        # Add the final section
        if last_pos < len(text):
            splits.append(text[last_pos:].strip())
        
        # If no good splits found or only one section, try a simpler approach
        if len(splits) <= 1:
            # Just split into roughly equal parts based on sentence boundaries
            sentences = re.split(r'(?<=[.!?]) +', text)
            if len(sentences) <= 3:
                return [text]  # Just one section if very short
            
            # Try to get 2-3 reasonably sized sections
            target_sections = min(3, max(2, len(sentences) // 5))
            section_size = len(sentences) // target_sections
            
            splits = []
            for i in range(target_sections):
                start = i * section_size
                end = (i + 1) * section_size if i < target_sections - 1 else len(sentences)
                section = ' '.join(sentences[start:end])
                splits.append(section)
        
        # Ensure all sections have enough content
        min_length = 50  # Minimum characters for a meaningful section
        return [s for s in splits if len(s) >= min_length]

    def clean_transcript(self, text: str) -> str:
        """Clean the transcript and format it properly"""
        # Remove any special markers
        text = re.sub(r'\[.*?\]', '', text)
        
        # Normalize spacing
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Break into reasonable lines (for readability)
        lines = textwrap.wrap(text, width=70)
        
        return '\n'.join(lines)

    def extract_questions_only(self, questions_text: str) -> str:
        """Extract only the questions without the multiple choice options"""
        questions_only = []
        
        # Match question patterns like "1. Question text?"
        question_pattern = re.compile(r'\d+\.\s+(.*?)\s*(?=A\)|$)', re.DOTALL)
        
        matches = question_pattern.findall(questions_text)
        
        # Format the questions
        for i, question in enumerate(matches):
            questions_only.append(f"{i+1}. {question.strip()}")
        
        return "\n\n".join(questions_only)

    def generate_title_and_questions(self, conversation: str) -> Tuple[str, str]:
        """Generate a title and questions from the transcript"""
        prompt = f"""Analysez ce dialogue en français (niveau DELF A1-A2).

Dialogue:
{conversation}

1. Donnez un titre descriptif (3-6 mots) pour ce dialogue, sans numéro de section.
2. Créez 2 questions simples (sans choix multiples) qui peuvent être répondues à partir du dialogue.

Utilisez exactement ce format:

Titre: [titre descriptif du dialogue]

Questions:

1. [question complète se terminant par un point d'interrogation]
2. [question complète se terminant par un point d'interrogation]
"""

        try:
            messages = [{
                "role": "user",
                "content": [{"text": prompt}]
            }]
            
            response = self.bedrock_client.converse(
                modelId=self.model_id,
                messages=messages,
                inferenceConfig={"temperature": 0.7}
            )
            
            result_text = response['output']['message']['content'][0]['text']
            
            # Extract title and questions
            title_match = re.search(r'Titre: (.*?)(?:\n|$)', result_text)
            title = title_match.group(1).strip() if title_match else "Dialogue en français"
            
            # Extract questions (everything after "Questions:")
            questions_match = re.search(r'Questions:(.*)', result_text, re.DOTALL)
            questions = questions_match.group(1).strip() if questions_match else ""
            
            return title, questions
            
        except Exception as e:
            print(f"Error generating title and questions: {str(e)}")
            return "Dialogue en français", "1. Question sur le dialogue?\n2. Question sur le dialogue?"

    def process_transcript_text(self, transcript_text: str) -> List[Dict[str, str]]:
        """Process plain text and generate Q&A for separate sections"""
        sections = self.split_transcript_into_sections(transcript_text)
        
        print(f"Split transcript into {len(sections)} sections")
        
        results = []
        for i, section in enumerate(sections):
            print(f"Processing section {i+1}/{len(sections)}...")
            
            cleaned_section = self.clean_transcript(section)
            
            # Generate title and questions for this section
            title, questions = self.generate_title_and_questions(cleaned_section)
            
            # Use the generated title directly as the introduction (without Section #)
            introduction = title
            
            # We're already getting simple questions without choices from the API
            # No need to extract them separately
            
            if questions:
                result = {
                    'section_num': i+1,
                    'introduction': introduction,
                    'conversation': cleaned_section,
                    'questions': questions
                }
                results.append(result)
                print(f"Successfully generated questions for section {i+1}")
            else:
                print(f"Failed to generate questions for section {i+1}")
        
        return results

    def process_transcript_files(self, transcript_dir: str) -> List[Dict[str, str]]:
        """Process all transcript files in the given directory"""
        all_results = []
        
        # Get all text files in the transcript directory
        file_paths = glob.glob(os.path.join(transcript_dir, "*.txt"))
        
        if not file_paths:
            print(f"No text files found in directory: {transcript_dir}")
            return all_results
        
        for i, file_path in enumerate(file_paths):
            file_name = os.path.basename(file_path)
            print(f"Processing file {i+1}/{len(file_paths)}: {file_name}")
            
            # Read the file content
            with open(file_path, 'r', encoding='utf-8') as f:
                transcript_text = f.read()
            
            # Process the transcript text
            file_results = self.process_transcript_text(transcript_text)
            
            # Add file information to the results
            for result in file_results:
                result['file_name'] = file_name
            
            all_results.extend(file_results)
            
        return all_results

    def save_results(self, results: List[Dict[str, str]], output_dir: str):
        """Save results to a file with the same name as the original file using the requested format"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Group results by file name
        grouped_results = {}
        for result in results:
            file_name = result['file_name']
            if file_name not in grouped_results:
                grouped_results[file_name] = []
            grouped_results[file_name].append(result)
        
        # Save one file per transcript, using the original file name
        for file_name, file_results in grouped_results.items():
            # Use the same name as the original file
            output_file = f"{output_dir}/{file_name}"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for result in file_results:
                    f.write(f"Introduction:\n{result['introduction']}\n\n")
                    f.write(f"Conversation:\n{result['conversation']}\n\n")
                    f.write(f"Questions:\n{result['questions']}\n\n")
                    f.write("-" * 50 + "\n\n")
            
            print(f"Saved questions to: {output_file}")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description="DELF French Listening Comprehension Question Generator")
    parser.add_argument("--transcript_dir", type=str, default="data/transcripts", 
                        help="Directory containing transcript files (default: data/transcripts)")
    # Output directory is now fixed to data/questions
    
    # Parse arguments
    args = parser.parse_args()
    
    print("DELF French Listening Comprehension Question Generator")
    print("-" * 50)
    
    # Initialize processor
    processor = FrenchTranscriptStructurer()
    
    # Use transcript directory from command line arguments or default to data/transcripts
    transcript_dir = args.transcript_dir if args.transcript_dir != "transcripts" else "data/transcripts"
    
    # Check if transcript directory exists
    print(f"\nUsing transcript directory: {transcript_dir}")
    
    if not os.path.isdir(transcript_dir):
        print(f"Directory '{transcript_dir}' does not exist.")
        print(f"Creating directory: {transcript_dir}")
        os.makedirs(transcript_dir, exist_ok=True)
        print(f"Please add your transcript files to {transcript_dir} and run the program again.")
        return
    
    # Process all transcript files
    results = processor.process_transcript_files(transcript_dir)
    
    if results:
        # Use the specified data/questions directory
        data_dir = "data/questions"
        print(f"\nSaving results to: {data_dir}")
        
        # Save results
        processor.save_results(results, data_dir)
        print(f"\nQuestions have been saved to the {data_dir} directory.")
    else:
        print("Failed to generate any questions!")

if __name__ == "__main__":
    main()