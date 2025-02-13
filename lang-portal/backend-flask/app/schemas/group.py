from dataclasses import dataclass
from typing import Dict, List

@dataclass
class GroupBaseSchema:
    id: int
    name: str
    word_count: int

@dataclass
class GroupDetailSchema(GroupBaseSchema):
    stats: Dict[str, int]

class GroupSchema:
    @staticmethod
    def basic(group) -> Dict:
        return {
            'id': group.id,
            'name': group.name,
            'word_count': len(group.words)
        }

    @staticmethod
    def detail(group) -> Dict:
        return {
            'id': group.id,
            'name': group.name,
            'stats': {
                'total_word_count': len(group.words)
            }
        }