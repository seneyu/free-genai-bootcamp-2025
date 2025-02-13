from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class WordBaseSchema:
    french: str
    english: str
    gender: Optional[str]
    parts: Dict

@dataclass
class WordWithStatsSchema(WordBaseSchema):
    correct_count: int
    wrong_count: int

@dataclass
class GroupBasicSchema:
    id: int
    name: str

@dataclass
class WordDetailSchema(WordWithStatsSchema):
    groups: List[GroupBasicSchema]

class WordSchema:
    @staticmethod
    def basic(word) -> Dict:
        return {
            'french': word.french,
            'english': word.english,
            'gender': word.gender,
            'parts': word.parts
        }

    @staticmethod
    def with_stats(word) -> Dict:
        correct_count = sum(1 for item in word.review_items if item.correct)
        wrong_count = sum(1 for item in word.review_items if not item.correct)
        return {
            'french': word.french,
            'english': word.english,
            'gender': word.gender,
            'parts': word.parts,
            'stats': {
                'correct_count': correct_count,
                'wrong_count': wrong_count
            }
        }

    @staticmethod
    def detail(word) -> Dict:
        base = WordSchema.with_stats(word)
        base['groups'] = [{'id': g.id, 'name': g.name} for g in word.groups]
        return base