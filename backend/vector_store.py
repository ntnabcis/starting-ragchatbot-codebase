"""
Vector storage module for semantic search using ChromaDB.

This module manages the persistence and retrieval of course content using
vector embeddings. It provides semantic search capabilities with intelligent
course name resolution and lesson filtering. The module maintains two separate
collections: one for course metadata and another for searchable content chunks.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from models import Course, CourseChunk
from sentence_transformers import SentenceTransformer


@dataclass
class SearchResults:
    """
    Container for search results from vector store queries.
    
    This dataclass provides a consistent interface for search results,
    regardless of the underlying storage implementation. It includes
    error handling and convenience methods for result processing.
    
    Attributes:
        documents: List of matching text content
        metadata: List of metadata dicts for each document
        distances: Similarity distances (lower = more similar)
        error: Optional error message if search failed
    """
    documents: List[str]
    metadata: List[Dict[str, Any]]
    distances: List[float]
    error: Optional[str] = None
    
    @classmethod
    def from_chroma(cls, chroma_results: Dict) -> 'SearchResults':
        """
        Factory method to create SearchResults from ChromaDB response.
        
        ChromaDB returns nested lists, so we extract the first element
        which contains our actual results.
        
        Args:
            chroma_results: Raw response from ChromaDB query
            
        Returns:
            SearchResults instance with parsed data
        """
        return cls(
            documents=chroma_results['documents'][0] if chroma_results['documents'] else [],
            metadata=chroma_results['metadatas'][0] if chroma_results['metadatas'] else [],
            distances=chroma_results['distances'][0] if chroma_results['distances'] else []
        )
    
    @classmethod
    def empty(cls, error_msg: str) -> 'SearchResults':
        """
        Factory method for creating empty results with an error.
        
        Used when search fails or no matching courses are found.
        
        Args:
            error_msg: Human-readable error description
            
        Returns:
            SearchResults with empty data and error message
        """
        return cls(documents=[], metadata=[], distances=[], error=error_msg)
    
    def is_empty(self) -> bool:
        """Check if results are empty"""
        return len(self.documents) == 0

class VectorStore:
    """
    Manages vector storage and semantic search for course materials.
    
    This class provides a high-level interface to ChromaDB, handling:
    1. Course metadata storage for intelligent name resolution
    2. Content chunk storage with embeddings for semantic search
    3. Filtered search by course and lesson
    4. Automatic embedding generation using sentence-transformers
    
    The dual-collection architecture separates course catalog information
    from searchable content, optimizing for different query patterns.
    
    Attributes:
        max_results: Default limit for search results
        client: ChromaDB persistent client instance
        embedding_function: Sentence transformer for generating embeddings
        course_catalog: Collection for course metadata
        course_content: Collection for searchable content chunks
    """
    
    def __init__(self, chroma_path: str, embedding_model: str, max_results: int = 5):
        """
        Initialize the vector store with ChromaDB backend.
        
        Args:
            chroma_path: Directory path for ChromaDB persistence
            embedding_model: HuggingFace model name for embeddings
            max_results: Default maximum results for searches
        """
        self.max_results = max_results
        
        # Initialize persistent ChromaDB client
        # Telemetry disabled for privacy
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Configure embedding generation
        # Using sentence-transformers for efficient semantic similarity
        self.embedding_function = chromadb.utils.embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model
        )
        
        # Initialize separate collections for different data types
        # This separation optimizes for different query patterns
        self.course_catalog = self._create_collection("course_catalog")  # For course discovery
        self.course_content = self._create_collection("course_content")  # For content search
    
    def _create_collection(self, name: str):
        """
        Create or retrieve a ChromaDB collection.
        
        Collections are created with the configured embedding function,
        ensuring consistent vector generation across all operations.
        
        Args:
            name: Collection identifier
            
        Returns:
            ChromaDB collection instance
        """
        return self.client.get_or_create_collection(
            name=name,
            embedding_function=self.embedding_function
        )
    
    def search(self, 
               query: str,
               course_name: Optional[str] = None,
               lesson_number: Optional[int] = None,
               limit: Optional[int] = None) -> SearchResults:
        """
        Perform semantic search with optional filtering.
        
        This method implements a two-phase search strategy:
        1. Course resolution: Fuzzy match course name to exact title
        2. Content search: Semantic search within filtered scope
        
        The course name resolution uses vector similarity, allowing
        partial matches like "MCP" to find "MCP Architecture Course".
        
        Args:
            query: Search query for semantic similarity matching
            course_name: Partial or full course name for filtering
            lesson_number: Specific lesson to search within
            limit: Override default result limit
            
        Returns:
            SearchResults with matched documents and metadata
            
        Performance Note:
            Course name resolution adds minimal latency (~10ms) but
            significantly improves search relevance when filtering.
        """
        # Phase 1: Intelligent course name resolution
        # Convert partial name to exact title using semantic similarity
        course_title = None
        if course_name:
            course_title = self._resolve_course_name(course_name)
            if not course_title:
                return SearchResults.empty(f"No course found matching '{course_name}'")
        
        # Phase 2: Build metadata filter for targeted search
        filter_dict = self._build_filter(course_title, lesson_number)
        
        # Phase 3: Execute semantic search with filters
        # Priority: explicit limit > configured default
        search_limit = limit if limit is not None else self.max_results
        
        try:
            results = self.course_content.query(
                query_texts=[query],
                n_results=search_limit,
                where=filter_dict
            )
            return SearchResults.from_chroma(results)
        except Exception as e:
            return SearchResults.empty(f"Search error: {str(e)}")
    
    def _resolve_course_name(self, course_name: str) -> Optional[str]:
        """
        Find the best matching course title using semantic similarity.
        
        This enables fuzzy matching where users can type partial names
        or abbreviations and still find the correct course.
        
        Args:
            course_name: User-provided course identifier (can be partial)
            
        Returns:
            Exact course title if found, None otherwise
            
        Example:
            "intro" might match "Introduction to Python Programming"
            "MCP" might match "MCP Architecture Fundamentals"
        """
        try:
            results = self.course_catalog.query(
                query_texts=[course_name],
                n_results=1  # Only need the best match
            )
            
            if results['documents'][0] and results['metadatas'][0]:
                # Extract exact title from metadata
                return results['metadatas'][0][0]['title']
        except Exception as e:
            print(f"Error resolving course name: {e}")
        
        return None
    
    def _build_filter(self, course_title: Optional[str], lesson_number: Optional[int]) -> Optional[Dict]:
        """
        Construct ChromaDB metadata filter for targeted search.
        
        Builds appropriate filter structure based on available parameters,
        supporting course-only, lesson-only, or combined filtering.
        
        Args:
            course_title: Resolved course title for filtering
            lesson_number: Lesson number for filtering
            
        Returns:
            ChromaDB filter dict or None for unfiltered search
            
        Filter Logic:
            - Both params: AND condition
            - Single param: Simple equality filter
            - No params: None (search all content)
        """
        if not course_title and lesson_number is None:
            return None  # No filtering needed
            
        # Combined filter for course AND lesson
        if course_title and lesson_number is not None:
            return {"$and": [
                {"course_title": course_title},
                {"lesson_number": lesson_number}
            ]}
        
        # Single filter for course OR lesson
        if course_title:
            return {"course_title": course_title}
            
        return {"lesson_number": lesson_number}
    
    def add_course_metadata(self, course: Course):
        """
        Index course metadata for intelligent name resolution.
        
        Stores course information in the catalog collection, enabling
        fuzzy search by course name. The course title serves as both
        the document content and the unique ID.
        
        Args:
            course: Course object with metadata to index
            
        Side Effects:
            - Adds/updates course in catalog collection
            - Course title becomes searchable immediately
            
        Note:
            Lessons are stored as JSON to preserve structure while
            keeping them queryable through the metadata system.
        """
        import json

        # Use title as searchable content for name resolution
        course_text = course.title
        
        # Build lessons metadata and serialize as JSON string
        lessons_metadata = []
        for lesson in course.lessons:
            lessons_metadata.append({
                "lesson_number": lesson.lesson_number,
                "lesson_title": lesson.title,
                "lesson_link": lesson.lesson_link
            })
        
        self.course_catalog.add(
            documents=[course_text],
            metadatas=[{
                "title": course.title,
                "instructor": course.instructor,
                "course_link": course.course_link,
                "lessons_json": json.dumps(lessons_metadata),  # Serialize as JSON string
                "lesson_count": len(course.lessons)
            }],
            ids=[course.title]
        )
    
    def add_course_content(self, chunks: List[CourseChunk]):
        """
        Index course content chunks for semantic search.
        
        Each chunk is stored with its text content and metadata,
        enabling filtered semantic search by course and lesson.
        IDs are generated to ensure uniqueness and traceability.
        
        Args:
            chunks: List of CourseChunk objects to index
            
        ID Generation:
            Format: "{course_title}_{chunk_index}"
            This ensures uniqueness and helps with debugging.
        """
        if not chunks:
            return  # Nothing to add
        
        documents = [chunk.content for chunk in chunks]
        metadatas = [{
            "course_title": chunk.course_title,
            "lesson_number": chunk.lesson_number,
            "chunk_index": chunk.chunk_index
        } for chunk in chunks]
        # Use title with chunk index for unique IDs
        ids = [f"{chunk.course_title.replace(' ', '_')}_{chunk.chunk_index}" for chunk in chunks]
        
        self.course_content.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
    
    def clear_all_data(self):
        """
        Remove all data and reset the vector store.
        
        This method completely deletes and recreates both collections,
        providing a clean slate for re-indexing. Use with caution as
        this operation is not reversible.
        
        Error Handling:
            Silently handles cases where collections don't exist.
        """
        try:
            # Delete existing collections
            self.client.delete_collection("course_catalog")
            self.client.delete_collection("course_content")
            # Recreate empty collections with same configuration
            self.course_catalog = self._create_collection("course_catalog")
            self.course_content = self._create_collection("course_content")
        except Exception as e:
            print(f"Error clearing data: {e}")
    
    def get_existing_course_titles(self) -> List[str]:
        """
        Retrieve all indexed course titles.
        
        Used to check for duplicates before adding new courses.
        Since course titles are used as IDs, this returns the ID list.
        
        Returns:
            List of course titles (may be empty)
            
        Error Recovery:
            Returns empty list on any error to allow graceful degradation.
        """
        try:
            # IDs in catalog are course titles
            results = self.course_catalog.get()
            if results and 'ids' in results:
                return results['ids']
            return []
        except Exception as e:
            print(f"Error getting existing course titles: {e}")
            return []
    
    def get_course_count(self) -> int:
        """Get the total number of courses in the vector store"""
        try:
            results = self.course_catalog.get()
            if results and 'ids' in results:
                return len(results['ids'])
            return 0
        except Exception as e:
            print(f"Error getting course count: {e}")
            return 0
    
    def get_all_courses_metadata(self) -> List[Dict[str, Any]]:
        """
        Retrieve complete metadata for all indexed courses.
        
        Fetches and deserializes all course information, including
        lesson structures. Used for generating statistics and course
        listings in the UI.
        
        Returns:
            List of course metadata dictionaries with parsed lessons
            
        Data Transformation:
            The stored JSON lesson data is parsed back into Python
            objects for easier consumption by the application.
        """
        import json
        try:
            results = self.course_catalog.get()
            if results and 'metadatas' in results:
                # Transform stored format to application format
                parsed_metadata = []
                for metadata in results['metadatas']:
                    course_meta = metadata.copy()
                    # Deserialize lesson data from JSON storage
                    if 'lessons_json' in course_meta:
                        course_meta['lessons'] = json.loads(course_meta['lessons_json'])
                        del course_meta['lessons_json']  # Clean up internal field
                    parsed_metadata.append(course_meta)
                return parsed_metadata
            return []
        except Exception as e:
            print(f"Error getting courses metadata: {e}")
            return []

    def get_course_link(self, course_title: str) -> Optional[str]:
        """Get course link for a given course title"""
        try:
            # Get course by ID (title is the ID)
            results = self.course_catalog.get(ids=[course_title])
            if results and 'metadatas' in results and results['metadatas']:
                metadata = results['metadatas'][0]
                return metadata.get('course_link')
            return None
        except Exception as e:
            print(f"Error getting course link: {e}")
            return None
    
    def get_lesson_link(self, course_title: str, lesson_number: int) -> Optional[str]:
        """
        Retrieve the URL link for a specific lesson.
        
        Searches within a course's lesson metadata to find the
        requested lesson and extract its link if available.
        
        Args:
            course_title: Exact course title (as stored)
            lesson_number: Lesson number to find
            
        Returns:
            Lesson URL if found, None otherwise
            
        Implementation:
            Deserializes lesson JSON and performs linear search.
            Efficient for typical course sizes (<100 lessons).
        """
        import json
        try:
            # Fetch course by exact title
            results = self.course_catalog.get(ids=[course_title])
            if results and 'metadatas' in results and results['metadatas']:
                metadata = results['metadatas'][0]
                lessons_json = metadata.get('lessons_json')
                if lessons_json:
                    lessons = json.loads(lessons_json)
                    # Linear search for matching lesson number
                    for lesson in lessons:
                        if lesson.get('lesson_number') == lesson_number:
                            return lesson.get('lesson_link')
            return None
        except Exception as e:
            print(f"Error getting lesson link: {e}")
    