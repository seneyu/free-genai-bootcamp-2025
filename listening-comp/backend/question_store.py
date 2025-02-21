import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import asdict, dataclass
from datetime import datetime

@dataclass
class StoredQuestion:
    id: str
    timestamp: str
    topic: str
    practice_type: str
    conversation: str
    questions: List[Dict[str, List[str]]]
    correct_answers: List[str]

class QuestionStore:
    def __init__(self):
        self.store_dir = Path(__file__).parent / "data" / "saved_questions"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.store_file = self.store_dir / "questions.json"
        
        # Create store file if it doesn't exist
        if not self.store_file.exists():
            self.store_file.write_text('[]')
    
    def save_question(self, topic: str, practice_type: str, exercise) -> str:
        """Save a generated question"""
        questions = self.load_all_questions()
        
        # Create new question ID based on timestamp
        question_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        new_question = StoredQuestion(
            id=question_id,
            timestamp=datetime.now().isoformat(),
            topic=topic,
            practice_type=practice_type,
            conversation=exercise.conversation,
            questions=exercise.questions,
            correct_answers=exercise.correct_answers
        )
        
        questions.append(asdict(new_question))
        
        # Save to file
        self.store_file.write_text(json.dumps(questions, indent=2))
        return question_id
    
    def load_all_questions(self) -> List[Dict]:
        """Load all saved questions"""
        try:
            return json.loads(self.store_file.read_text())
        except Exception:
            return []
    
    def load_question(self, question_id: str) -> Optional[StoredQuestion]:
        """Load a specific question by ID"""
        questions = self.load_all_questions()
        for q in questions:
            if q['id'] == question_id:
                return StoredQuestion(**q)
        return None 