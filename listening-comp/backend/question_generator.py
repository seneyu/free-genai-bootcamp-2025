from typing import Dict, List, Optional
from dataclasses import dataclass
from .vector_store import FrenchQuestionVectorStore
from .chat import BedrockChat
import random
import re

@dataclass
class GeneratedQuestion:
    conversation: str
    questions: List[Dict[str, List[str]]]  # Each question has the question text and options
    correct_answers: List[str]  # Add correct answers field

class QuestionGenerator:
    def __init__(self):
        self.vector_store = FrenchQuestionVectorStore()
        self.chat = BedrockChat()
        
    TOPICS = {
        "Daily Life": "la vie quotidienne",
        "Food & Restaurant": "la nourriture et le restaurant",
        "Travel": "le voyage",
        "Shopping": "les achats",
        "Family": "la famille",
        "Hobbies": "les loisirs",
        "Weather": "la météo",
        "Work": "le travail"
    }

    def generate_practice_question(self, practice_type: str, topic: str) -> Optional[GeneratedQuestion]:
        """Generate a practice question with multiple choice options"""
        # Get search query based on practice type and topic
        topic_fr = self.TOPICS.get(topic, "général")
        search_query = f"{practice_type.lower()} about {topic.lower()}"
        
        # Search for similar questions
        similar_questions = self.vector_store.search_similar_questions(search_query, n_results=3)
        
        # Create context from similar questions
        context = "\n\n".join([
            f"Exemple {i+1}:\n" +
            f"Dialogue: {q['conversation']}\n" +
            f"Questions: {q['questions']}"
            for i, q in enumerate(similar_questions)
        ])
        
        # Instead of pre-determining answers, let the model create accurate answers based on the dialogue
        prompt = f"""En utilisant ces exemples d'exercices comme inspiration, créez un dialogue sur le thème: {topic_fr}

{context}

Créez un nouvel exercice avec:
1. Un court dialogue en français (niveau A1-A2) sur le thème donné
2. 2 questions de compréhension en français (pas plus)
3. Pour chaque question, créez 4 options (A, B, C, D) en français
4. IMPORTANT: Pour chaque question, la réponse correcte DOIT correspondre précisément au contenu du dialogue.

Format de réponse:
DIALOGUE:
[le dialogue]

QUESTIONS:
1. [question 1]
   A) [option A]
   B) [option B]
   C) [option C]
   D) [option D]

2. [question 2]
   A) [option A]
   B) [option B]
   C) [option C]
   D) [option D]

REPONSES:
1:[lettre de la réponse correcte pour question 1]
2:[lettre de la réponse correcte pour question 2]"""

        response = self.chat.generate_response(prompt)
        
        # Parse the response into structured format
        try:
            # Check if response contains all expected sections
            if "DIALOGUE:" not in response or "QUESTIONS:" not in response or "REPONSES:" not in response:
                print("Response does not contain all required sections.")
                print(f"Response preview: {response[:200]}...")
                return None
                
            # Extract dialogue section
            dialogue_match = re.search(r"DIALOGUE:(.*?)QUESTIONS:", response, re.DOTALL)
            if not dialogue_match:
                print("Could not extract dialogue section")
                return None
            dialogue_part = dialogue_match.group(1).strip()
            
            # Extract questions section
            questions_match = re.search(r"QUESTIONS:(.*?)REPONSES:", response, re.DOTALL)
            if not questions_match:
                print("Could not extract questions section")
                return None
            questions_part = questions_match.group(1).strip()
            
            # Extract answers section
            answers_match = re.search(r"REPONSES:(.*?)$", response, re.DOTALL)
            if not answers_match:
                print("Could not extract answers section")
                return None
            answers_part = answers_match.group(1).strip()
            
            # Parse questions and options
            questions = []
            question_pattern = r"(\d+)\.\s+(.*?)(?=\d+\.|$)"
            option_pattern = r"([A-D])\)\s+(.*?)(?=[A-D]\)|$)"
            
            # Find all questions
            question_matches = re.finditer(question_pattern, questions_part, re.DOTALL)
            
            for q_match in question_matches:
                question_number = q_match.group(1)
                question_text = q_match.group(2).strip()
                
                # Find the options for this question
                options_text = question_text
                question_text = re.sub(r"[A-D]\).*", "", question_text, flags=re.DOTALL).strip()
                
                # Extract options
                option_matches = re.finditer(option_pattern, options_text, re.DOTALL)
                options = []
                
                for o_match in option_matches:
                    option_text = o_match.group(2).strip()
                    options.append(option_text)
                
                # Ensure we have 4 options
                while len(options) < 4:
                    options.append(f"Option {len(options)+1}")
                
                questions.append({
                    'question': question_text,
                    'options': options[:4]  # Take at most 4 options
                })
            
            # Ensure we have at least 1 question
            if not questions:
                print("No questions found in the response")
                return None
                
            # Limit to 2 questions
            questions = questions[:2]
            
            # Parse answers
            correct_answers = []
            for line in answers_part.split('\n'):
                line = line.strip()
                if line:
                    # Extract the answer (letter after the colon)
                    match = re.search(r"\d+:([A-D])", line)
                    if match:
                        answer = match.group(1)
                        correct_answers.append(answer)
            
            # Ensure we have answers for all questions
            if len(correct_answers) < len(questions):
                print("Warning: Not enough correct answers provided. Adding default answers.")
                # Add more robust fallback for missing answers
                while len(correct_answers) < len(questions):
                    # Look for an answer in the dialogue
                    missing_q_index = len(correct_answers)
                    missing_q = questions[missing_q_index]
                    
                    # Try to find which option actually matches the dialogue content
                    for idx, option in enumerate(['A', 'B', 'C', 'D']):
                        option_text = missing_q['options'][idx] if idx < len(missing_q['options']) else ""
                        # Simple heuristic: if the option text appears in the dialogue, it might be correct
                        if option_text and option_text.lower() in dialogue_part.lower():
                            correct_answers.append(option)
                            print(f"Auto-detected answer for question {missing_q_index+1}: {option}")
                            break
                    else:
                        # If no match found, default to 'A'
                        correct_answers.append('A')
                        print(f"Defaulting to 'A' for question {missing_q_index+1}")
                        
            # Validate answers against the dialogue
            for i, (question, answer) in enumerate(zip(questions, correct_answers)):
                answer_idx = ord(answer) - ord('A')
                if answer_idx < len(question['options']):
                    option_text = question['options'][answer_idx]
                    # Log for debugging
                    print(f"Q{i+1}: {question['question']}")
                    print(f"Answer: {answer}) {option_text}")
                
            return GeneratedQuestion(
                conversation=dialogue_part,
                questions=questions,
                correct_answers=correct_answers[:len(questions)]  # Match number of answers to questions
            )
            
        except Exception as e:
            print(f"Error parsing response: {str(e)}")
            print(f"Response preview: {response[:200]}...")
            return None