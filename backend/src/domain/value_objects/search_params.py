from typing import Optional
from dataclasses import dataclass


@dataclass(frozen=True)
class SearchParams:
    query: str
    course_name: Optional[str] = None
    lesson_number: Optional[int] = None
    limit: int = 5
    
    def __post_init__(self):
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if self.lesson_number is not None and self.lesson_number < 0:
            raise ValueError("Lesson number must be non-negative")
    
    def to_filter_dict(self) -> Optional[dict]:
        if not self.course_name and self.lesson_number is None:
            return None
        
        filters = {}
        if self.course_name:
            filters['course_title'] = self.course_name
        if self.lesson_number is not None:
            filters['lesson_number'] = self.lesson_number
        
        if len(filters) > 1:
            return {"$and": [
                {key: value} for key, value in filters.items()
            ]}
        
        return filters