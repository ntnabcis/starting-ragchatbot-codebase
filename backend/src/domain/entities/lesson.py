"""
Lesson entity for course content organization.

Represents individual lessons within a course structure.
Provides metadata and serialization for lesson management.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class Lesson:
    """
    Domain entity representing a course lesson.
    
    Encapsulates lesson metadata and provides identity management.
    Serves as a value object within the Course aggregate.
    
    Attributes:
        lesson_number: Sequential lesson identifier within course
        title: Descriptive lesson name
        lesson_link: Optional URL to lesson materials
        
    Design Patterns:
        - Immutable value object pattern (dataclass frozen could be added)
        - Natural composite key (lesson_number + title)
    """
    lesson_number: int
    title: str
    lesson_link: Optional[str] = None
    
    @property
    def id(self) -> str:
        """
        Generate unique lesson identifier.
        
        Returns:
            String formatted as 'lesson_X' where X is lesson number
            
        Example:
            Lesson 5 -> "lesson_5"
        """
        return f"lesson_{self.lesson_number}"
    
    def to_dict(self) -> dict:
        """
        Serialize lesson to dictionary for persistence.
        
        Returns:
            Dictionary containing all lesson attributes
            
        Format:
            Simple flat structure suitable for JSON serialization.
        """
        return {
            'lesson_number': self.lesson_number,
            'title': self.title,
            'lesson_link': self.lesson_link
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Lesson':
        """
        Deserialize lesson from dictionary.
        
        Args:
            data: Dictionary containing lesson data
            
        Returns:
            Lesson instance reconstructed from data
            
        Handles:
            Optional lesson_link field with None default.
        """
        return cls(
            lesson_number=data['lesson_number'],
            title=data['title'],
            lesson_link=data.get('lesson_link')
        )
    
    def __eq__(self, other):
        """
        Check lesson equality based on number and title.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if both lessons have same number and title
            
        Note:
            Both lesson_number and title form composite key.
        """
        if not isinstance(other, Lesson):
            return False
        return self.lesson_number == other.lesson_number and self.title == other.title
    
    def __hash__(self):
        """
        Generate hash from composite key.
        
        Returns:
            Hash of (lesson_number, title) tuple
            
        Consistency:
            Matches equality - same number/title yields same hash.
        """
        return hash((self.lesson_number, self.title))