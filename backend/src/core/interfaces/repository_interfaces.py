"""
Repository interface definitions for data access layer.

This module defines abstract base classes that establish contracts for data persistence.
Following the Repository pattern, these interfaces decouple business logic from data access
implementation details, enabling easy swapping of storage backends.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CourseData:
    """
    Data transfer object for course information.
    
    Represents a lightweight course structure for repository operations,
    containing only essential data without business logic.
    
    Attributes:
        title: Unique course identifier and display name
        course_link: Optional URL to course materials
        instructor: Optional instructor name
        lessons: List of lesson metadata dictionaries
    """
    title: str
    course_link: Optional[str] = None
    instructor: Optional[str] = None
    lessons: List[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize empty lessons list if None provided."""
        if self.lessons is None:
            self.lessons = []


@dataclass
class SessionData:
    """
    Data transfer object for conversation session data.
    
    Attributes:
        session_id: Unique session identifier
        messages: Chronological list of conversation messages with role and content
    """
    session_id: str
    messages: List[Dict[str, str]]


class ICourseRepository(ABC):
    """
    Abstract interface for course data persistence.
    
    Defines contract for storing and retrieving course metadata.
    Implementations might use databases, file systems, or cloud storage.
    """
    
    @abstractmethod
    async def get_course_by_title(self, title: str) -> Optional[CourseData]:
        """
        Retrieve course by its title.
        
        Args:
            title: Exact course title to search for
            
        Returns:
            CourseData if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_all_courses(self) -> List[CourseData]:
        """
        Retrieve all courses from storage.
        
        Returns:
            List of all stored courses, empty list if none exist
        """
        pass
    
    @abstractmethod
    async def save_course(self, course: CourseData) -> bool:
        """
        Persist course data to storage.
        
        Args:
            course: Course data to save
            
        Returns:
            True if successful, False on failure
        """
        pass
    
    @abstractmethod
    async def course_exists(self, title: str) -> bool:
        """
        Check if course with given title exists.
        
        Args:
            title: Course title to check
            
        Returns:
            True if course exists, False otherwise
        """
        pass
    
    @abstractmethod
    async def get_course_count(self) -> int:
        """
        Get total number of courses in storage.
        
        Returns:
            Count of all courses
        """
        pass


class IDocumentRepository(ABC):
    """
    Abstract interface for document chunk persistence.
    
    Manages storage and retrieval of processed document chunks
    used for semantic search operations.
    """
    
    @abstractmethod
    async def save_document_chunks(self, chunks: List[Dict[str, Any]]) -> bool:
        """
        Save multiple document chunks in batch.
        
        Args:
            chunks: List of chunk dictionaries containing content and metadata
            
        Returns:
            True if all chunks saved successfully, False on any failure
            
        Note:
            Implementations should handle batch operations efficiently
            to prevent memory issues with large document sets.
        """
        pass
    
    @abstractmethod
    async def get_chunks_by_course(self, course_title: str) -> List[Dict[str, Any]]:
        """
        Retrieve all chunks belonging to a specific course.
        
        Args:
            course_title: Title of the course to filter by
            
        Returns:
            List of chunk dictionaries for the specified course
        """
        pass
    
    @abstractmethod
    async def search_chunks(self, query: str, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Search chunks using semantic or keyword search.
        
        Args:
            query: Search query text
            filters: Optional filter criteria (e.g., course, lesson number)
            
        Returns:
            List of matching chunks ordered by relevance
            
        Note:
            Implementation typically uses vector similarity search
            for semantic matching of query against chunk content.
        """
        pass


class ISessionRepository(ABC):
    """
    Abstract interface for conversation session management.
    
    Handles persistence of user conversation sessions and message history
    to maintain context across multiple interactions.
    """
    
    @abstractmethod
    async def create_session(self) -> str:
        """
        Create new conversation session.
        
        Returns:
            Unique session identifier
            
        Note:
            Session IDs should be globally unique and URL-safe.
        """
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Retrieve session data by ID.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            SessionData if found, None for invalid/expired sessions
        """
        pass
    
    @abstractmethod
    async def save_message(self, session_id: str, role: str, content: str) -> bool:
        """
        Append message to session history.
        
        Args:
            session_id: Target session identifier
            role: Message role ('user', 'assistant', or 'system')
            content: Message text content
            
        Returns:
            True if saved successfully, False on failure
            
        Side Effects:
            Creates session if it doesn't exist
            May trigger history trimming if limit exceeded
        """
        pass
    
    @abstractmethod
    async def get_session_history(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """
        Retrieve recent message history for session.
        
        Args:
            session_id: Session to retrieve history for
            limit: Maximum number of messages to return
            
        Returns:
            List of message dictionaries with 'role' and 'content' keys,
            ordered chronologically (oldest first)
            
        Note:
            Returns empty list for non-existent sessions rather than error.
        """
        pass
    
    @abstractmethod
    async def clear_session(self, session_id: str) -> bool:
        """
        Clear all messages from session while preserving session ID.
        
        Args:
            session_id: Session to clear
            
        Returns:
            True if cleared successfully, False if session doesn't exist
            
        Use Case:
            Allows users to reset conversation context without losing session.
        """
        pass