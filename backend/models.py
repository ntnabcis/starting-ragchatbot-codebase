"""
Data models for the Course Materials RAG System.

This module defines the core data structures used throughout the application
for representing courses, lessons, and document chunks. All models use Pydantic
for automatic validation, serialization, and type checking.
"""

from typing import List, Dict, Optional
from pydantic import BaseModel


class Lesson(BaseModel):
    """
    Represents a single lesson within a course.
    
    This model captures the essential metadata for a lesson, including its
    sequential position and title. The lesson_number is used for ordering
    and filtering during search operations.
    
    Attributes:
        lesson_number: Sequential identifier (1-based) for lesson ordering
        title: Human-readable lesson title for display and search
        lesson_link: Optional URL for external lesson resources
    """
    lesson_number: int  # 1-based indexing for user-friendly display
    title: str         # Used in search results to provide context
    lesson_link: Optional[str] = None  # External resource link if available


class Course(BaseModel):
    """
    Represents a complete course with its metadata and lesson structure.
    
    The Course model serves as the top-level container for educational content.
    The title field acts as a unique identifier throughout the system, so
    duplicate course titles should be avoided during document processing.
    
    Attributes:
        title: Unique course identifier and display name
        course_link: Optional URL to the full course material
        instructor: Optional instructor name for attribution
        lessons: Ordered list of lessons belonging to this course
    
    Note:
        The course title is used as a primary key in vector storage,
        so it must be unique across all courses in the system.
    """
    title: str                 # Primary identifier - must be unique
    course_link: Optional[str] = None  # External course homepage
    instructor: Optional[str] = None  # Metadata for filtering/display
    lessons: List[Lesson] = [] # Maintains lesson order from source


class CourseChunk(BaseModel):
    """
    Represents a searchable text chunk from course content.
    
    This model is the atomic unit for vector storage and semantic search.
    Documents are split into chunks to fit within embedding model limits
    and to provide focused search results. Each chunk maintains references
    to its source course and lesson for context reconstruction.
    
    Attributes:
        content: The actual text to be embedded and searched
        course_title: Reference to parent course for filtering
        lesson_number: Optional reference to specific lesson
        chunk_index: Sequential position for maintaining document order
    
    Design Rationale:
        Chunks are sized (see config.CHUNK_SIZE) to balance between:
        - Semantic coherence (not too small)
        - Search precision (not too large)
        - API token limits (fits in context window)
    """
    content: str                        # Text that will be embedded for search
    course_title: str                   # Foreign key to Course.title
    lesson_number: Optional[int] = None # Foreign key to Lesson.lesson_number
    chunk_index: int                    # Preserves original document order