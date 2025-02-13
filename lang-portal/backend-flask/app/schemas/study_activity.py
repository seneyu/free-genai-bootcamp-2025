from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime

@dataclass
class StudyActivitySchema:
    id: int
    name: str
    thumbnail_url: Optional[str]
    description: Optional[str]

    @staticmethod
    def from_model(activity) -> Dict:
        return {
            'id': activity.id,
            'name': activity.name,
            'thumbnail_url': activity.thumbnail_url,
            'description': activity.description
        }

    @staticmethod
    def basic(activity) -> Dict:
        return {
            'id': activity.id,
            'name': activity.name,
            'thumbnail_url': activity.thumbnail_url,
            'description': activity.description
        }