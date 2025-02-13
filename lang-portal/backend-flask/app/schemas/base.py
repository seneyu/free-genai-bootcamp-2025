from dataclasses import dataclass
from typing import List, Dict, Optional, Any

@dataclass
class PaginationSchema:
    current_page: int
    total_pages: int
    total_items: int
    items_per_page: int

    @classmethod
    def create(cls, page: int, per_page: int, total: int) -> Dict:
        return {
            'current_page': page,
            'total_pages': (total + per_page - 1) // per_page,
            'total_items': total,
            'items_per_page': per_page
        }