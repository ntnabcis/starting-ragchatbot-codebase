"""
Course entity for educational content management.

Represents a complete course with metadata and associated lessons.
Serves as the primary aggregate root for course-related operations.
"""

from typing import List, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .lesson import Lesson


@dataclass
class Course:
    """
    Domain entity representing an educational course.
    
    Encapsulates course metadata and manages associated lessons.
    Provides business logic for course operations and data transformations.
    
    Attributes:
        title: Unique course name serving as natural key
        course_link: Optional URL to external course resources
        instructor: Optional name of course instructor
        lessons: Ordered list of course lessons
        created_at: Timestamp of course creation
        updated_at: Timestamp of last modification
        
    Design Decisions:
        - Uses title as natural key for simplicity and readability
        - Lessons automatically sorted by lesson_number for consistency
        - Timestamps updated automatically on modifications
    """
    title: str
    course_link: Optional[str] = None
    instructor: Optional[str] = None
    lessons: List[Lesson] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def id(self) -> str:
        """
        Generate URL-safe identifier from course title.
        
        Returns:
            Lowercase, underscore-separated version of title
            
        Example:
            "Machine Learning 101" -> "machine_learning_101"
        """
        return self.title.lower().replace(' ', '_')
    
    @property
    def lesson_count(self) -> int:
        """
        Get total number of lessons in course.
        
        Returns:
            Count of lessons
        """
        return len(self.lessons)
    
    def add_lesson(self, lesson: Lesson) -> None:
        """
        Add lesson to course if not already present.
        
        Args:
            lesson: Lesson instance to add
            
        Side Effects:
            - Appends lesson if not duplicate
            - Re-sorts lessons by lesson_number
            - Updates timestamp
            
        Note:
            Duplicate detection based on lesson equality (lesson_number).
        """
        if lesson not in self.lessons:
            self.lessons.append(lesson)
            # Maintain sorted order for consistent access
            self.lessons.sort(key=lambda x: x.lesson_number)
            self.updated_at = datetime.now()
    
    def get_lesson(self, lesson_number: int) -> Optional[Lesson]:
        """
        Retrieve specific lesson by number.
        
        Args:
            lesson_number: Lesson number to find
            
        Returns:
            Lesson if found, None otherwise
            
        Performance Note:
            Linear search acceptable for typical course sizes (< 100 lessons).
        """
        for lesson in self.lessons:
            if lesson.lesson_number == lesson_number:
                return lesson
        return None
    
    def to_dict(self) -> dict:
        """
        Serialize course to dictionary for persistence.
        
        Returns:
            Dictionary with all course data including nested lessons
            
        Format:
            Timestamps converted to ISO format for JSON compatibility.
            Lessons recursively serialized.
        """
        return {
            'title': self.title,
            'course_link': self.course_link,
            'instructor': self.instructor,
            'lessons': [lesson.to_dict() for lesson in self.lessons],
            'lesson_count': self.lesson_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Course':
        """
        Deserialize course from dictionary.
        
        Args:
            data: Dictionary containing course data
            
        Returns:
            Course instance reconstructed from data
            
        Handles:
            - Missing optional fields with defaults
            - Recursive lesson deserialization
            - Timestamp parsing from ISO format
        """
        # Recursively deserialize lessons
        lessons = [Lesson.from_dict(lesson_data) for lesson_data in data.get('lessons', [])]
        return cls(
            title=data['title'],
            course_link=data.get('course_link'),
            instructor=data.get('instructor'),
            lessons=lessons,
            created_at=datetime.fromisoformat(data.get('created_at', datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(data.get('updated_at', datetime.now().isoformat()))
        )
    
    def __eq__(self, other):
        """
        Check course equality based on title.
        
        Args:
            other: Object to compare with
            
        Returns:
            True if both are courses with same title
            
        Note:
            Title serves as natural key for course identity.
        """
        if not isinstance(other, Course):
            return False
        return self.title == other.title
    
    def __hash__(self):
        """
        Generate hash based on course title.
        
        Returns:
            Hash of title for use in sets/dicts
            
        Consistency:
            Matches equality - courses with same title have same hash.
        """
        return hash(self.title)