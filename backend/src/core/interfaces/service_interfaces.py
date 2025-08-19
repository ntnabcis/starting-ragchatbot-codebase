"""
Service interface definitions for business logic layer.

This module defines abstract interfaces for core application services.
These interfaces establish contracts for document processing, search operations,
AI integration, and embedding generation, enabling flexible implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path


class IDocumentProcessor(ABC):
    """
    Abstract interface for document processing operations.
    
    Handles parsing, chunking, and structuring of raw documents
    into formats suitable for vector storage and retrieval.
    """
    
    @abstractmethod
    async def process_document(self, file_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process a document file into structured course data and chunks.
        
        Args:
            file_path: Path to the document file to process
            
        Returns:
            Tuple containing:
                - Course metadata dictionary with title, instructor, lessons
                - List of chunk dictionaries ready for vector storage
                
        Raises:
            FileNotFoundError: If file_path doesn't exist
            ValueError: If document format is invalid
            
        Note:
            Expected document format should follow course structure with
            metadata headers and lesson markers.
        """
        pass
    
    @abstractmethod
    def chunk_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Split text into overlapping chunks for vector embedding.
        
        Args:
            text: Input text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks with specified overlap
            
        Design Rationale:
            Overlapping chunks ensure context isn't lost at boundaries,
            improving semantic search accuracy.
        """
        pass


class ISearchService(ABC):
    """
    Abstract interface for search and retrieval operations.
    
    Provides semantic and metadata-based search capabilities
    across document chunks and course information.
    """
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        course_name: Optional[str] = None,
        lesson_number: Optional[int] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Perform semantic search across document chunks.
        
        Args:
            query: Search query text
            course_name: Optional course name for filtering (fuzzy matched)
            lesson_number: Optional specific lesson to search within
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing:
                - 'success': Boolean indicating search success
                - 'results': List of matching chunks with metadata
                - 'total': Total number of results found
                - 'error': Error message if search failed
                
        Performance Considerations:
            - Course name uses fuzzy matching for user convenience
            - Results ranked by semantic similarity scores
            - Limit prevents memory issues with large result sets
        """
        pass
    
    @abstractmethod
    async def get_similar_courses(self, course_name: str, limit: int = 5) -> List[str]:
        """
        Find courses with names similar to the query.
        
        Args:
            course_name: Partial or full course name to match
            limit: Maximum number of suggestions
            
        Returns:
            List of course titles sorted by similarity
            
        Use Case:
            Helps users find courses when they don't know exact titles,
            supporting typo tolerance and partial matching.
        """
        pass


class IAIService(ABC):
    """
    Abstract interface for AI language model integration.
    
    Defines contract for generating intelligent responses using
    large language models with context and conversation history.
    """
    
    @abstractmethod
    async def generate_response(
        self,
        query: str,
        context: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        tools: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate AI response for user query.
        
        Args:
            query: User's question or prompt
            context: Retrieved document context for RAG
            conversation_history: Previous messages for continuity
            tools: Optional tool definitions for function calling
            
        Returns:
            Generated response text
            
        Side Effects:
            May invoke tool functions if provided
            Updates internal token usage metrics
            
        Error Handling:
            Returns graceful error message on API failures
            rather than raising exceptions to maintain UX.
        """
        pass
    
    @abstractmethod
    def set_system_prompt(self, prompt: str) -> None:
        """
        Configure the system prompt for the AI model.
        
        Args:
            prompt: System instructions defining AI behavior
            
        Design Note:
            System prompt shapes response style, expertise level,
            and conversation boundaries.
        """
        pass


class IEmbeddingService(ABC):
    """
    Abstract interface for text embedding generation.
    
    Converts text into dense vector representations for
    semantic similarity calculations and vector search.
    """
    
    @abstractmethod
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate vector embedding for single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            Dense vector representation (typically 384-1536 dimensions)
            
        Note:
            Empty list returned on errors to prevent downstream failures.
        """
        pass
    
    @abstractmethod
    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings corresponding to input texts
            
        Performance Optimization:
            Batch processing reduces model loading overhead
            and improves throughput for large document sets.
        """
        pass