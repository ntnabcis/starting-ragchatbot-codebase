"""
Core RAG system orchestrator module.

This module implements the main RAG (Retrieval-Augmented Generation) system
that coordinates all components: document processing, vector storage, AI
generation, session management, and tool-based search. It provides the primary
interface for the FastAPI application to interact with the RAG functionality.
"""

from typing import List, Tuple, Optional, Dict
import os
from document_processor import DocumentProcessor
from vector_store import VectorStore
from ai_generator import AIGenerator
from session_manager import SessionManager
from search_tools import ToolManager, CourseSearchTool
from models import Course, Lesson, CourseChunk


class RAGSystem:
    """
    Main orchestrator for the Retrieval-Augmented Generation system.
    
    This class integrates all RAG components into a cohesive system,
    managing the flow from document ingestion through query processing
    to response generation. It implements a tool-based architecture where
    the AI can autonomously decide when to search for information.
    
    The system supports:
    - Document ingestion and chunking
    - Semantic search with intelligent filtering
    - Context-aware AI response generation
    - Conversation history management
    - Tool-based autonomous search
    
    Attributes:
        config: Configuration object with system settings
        document_processor: Handles document parsing and chunking
        vector_store: Manages vector storage and retrieval
        ai_generator: Interfaces with Claude for response generation
        session_manager: Tracks conversation history
        tool_manager: Manages available AI tools
        search_tool: Concrete tool for course content search
    """
    
    def __init__(self, config):
        """
        Initialize the RAG system with configuration.
        
        Sets up all components with appropriate configuration and
        establishes the tool-based search architecture.
        
        Args:
            config: Config object with all system settings
        """
        self.config = config
        
        # Initialize core RAG components with configured parameters
        self.document_processor = DocumentProcessor(config.CHUNK_SIZE, config.CHUNK_OVERLAP)
        self.vector_store = VectorStore(config.CHROMA_PATH, config.EMBEDDING_MODEL, config.MAX_RESULTS)
        self.ai_generator = AIGenerator(config.ANTHROPIC_API_KEY, config.ANTHROPIC_MODEL)
        self.session_manager = SessionManager(config.MAX_HISTORY)
        
        # Set up tool-based search architecture
        # This allows AI to autonomously decide when to search
        self.tool_manager = ToolManager()
        self.search_tool = CourseSearchTool(self.vector_store)
        self.tool_manager.register_tool(self.search_tool)
    
    def add_course_document(self, file_path: str) -> Tuple[Course, int]:
        """
        Process and index a single course document.
        
        This method handles the complete ingestion pipeline:
        1. Parse document structure and extract metadata
        2. Chunk content for optimal retrieval
        3. Generate embeddings and store in vector database
        
        Args:
            file_path: Path to the course document file
            
        Returns:
            Tuple containing:
            - Course object with metadata (or None on error)
            - Number of chunks created (0 on error)
            
        Error Handling:
            Catches and logs exceptions to prevent system crashes
            Returns (None, 0) on failure for graceful degradation
        """
        try:
            # Phase 1: Document processing and chunking
            course, course_chunks = self.document_processor.process_course_document(file_path)
            
            # Phase 2: Index course metadata for name resolution
            self.vector_store.add_course_metadata(course)
            
            # Phase 3: Index content chunks for semantic search
            self.vector_store.add_course_content(course_chunks)
            
            return course, len(course_chunks)
        except Exception as e:
            print(f"Error processing course document {file_path}: {e}")
            return None, 0  # Graceful failure
    
    def add_course_folder(self, folder_path: str, clear_existing: bool = False) -> Tuple[int, int]:
        """
        Batch process all course documents in a folder.
        
        Supports incremental updates (default) or full rebuilds.
        Automatically detects and skips already-indexed courses
        to avoid duplicates and save processing time.
        
        Args:
            folder_path: Directory containing course documents
            clear_existing: If True, removes all existing data first
            
        Returns:
            Tuple containing:
            - Number of new courses added
            - Total number of chunks created
            
        Supported Formats:
            - .txt (primary format)
            - .pdf (future extension)
            - .docx (future extension)
            
        Performance:
            Duplicate detection uses course titles as unique keys,
            preventing redundant processing and storage.
        """
        total_courses = 0
        total_chunks = 0
        
        # Optional full rebuild - clears all existing data
        if clear_existing:
            print("Clearing existing data for fresh rebuild...")
            self.vector_store.clear_all_data()
        
        # Validate folder exists
        if not os.path.exists(folder_path):
            print(f"Folder {folder_path} does not exist")
            return 0, 0
        
        # Build set of existing courses for O(1) duplicate detection
        existing_course_titles = set(self.vector_store.get_existing_course_titles())
        
        # Process each file in the folder
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path) and file_name.lower().endswith(('.pdf', '.docx', '.txt')):
                try:
                    # Process document to extract course information
                    course, course_chunks = self.document_processor.process_course_document(file_path)
                    
                    if course and course.title not in existing_course_titles:
                        # New course detected - add to knowledge base
                        self.vector_store.add_course_metadata(course)
                        self.vector_store.add_course_content(course_chunks)
                        total_courses += 1
                        total_chunks += len(course_chunks)
                        print(f"Added new course: {course.title} ({len(course_chunks)} chunks)")
                        # Update tracking set to prevent re-processing in same batch
                        existing_course_titles.add(course.title)
                    elif course:
                        # Course already indexed - skip to save resources
                        print(f"Course already exists: {course.title} - skipping")
                except Exception as e:
                    # Log error but continue processing other files
                    print(f"Error processing {file_name}: {e}")
        
        return total_courses, total_chunks
    
    def query(self, query: str, session_id: Optional[str] = None) -> Tuple[str, List[str]]:
        """
        Process a user query through the complete RAG pipeline.
        
        This method orchestrates the query processing flow:
        1. Retrieve conversation history for context
        2. Allow AI to autonomously use search tools
        3. Generate contextual response
        4. Track sources for attribution
        5. Update conversation history
        
        The tool-based approach means the AI decides whether to search,
        rather than always retrieving context upfront.
        
        Args:
            query: User's question or request
            session_id: Optional identifier for conversation continuity
            
        Returns:
            Tuple containing:
            - AI-generated response text
            - List of source citations (course/lesson references)
            
        Flow:
            Query -> [History] -> AI Decision -> [Tool Use] -> Response
        """
        # Format query with clear context for the AI
        prompt = f"""Answer this question about course materials: {query}"""
        
        # Retrieve conversation context for coherent multi-turn dialogue
        history = None
        if session_id:
            history = self.session_manager.get_conversation_history(session_id)
        
        # Execute AI generation with tool support
        # AI autonomously decides whether to search
        response = self.ai_generator.generate_response(
            query=prompt,
            conversation_history=history,
            tools=self.tool_manager.get_tool_definitions(),
            tool_manager=self.tool_manager
        )
        
        # Extract source citations from tool usage
        sources = self.tool_manager.get_last_sources()

        # Clear sources to prevent cross-query contamination
        self.tool_manager.reset_sources()
        
        # Persist conversation for context in future queries
        if session_id:
            self.session_manager.add_exchange(session_id, query, response)
        
        # Return AI response with source attributions
        return response, sources
    
    def get_course_analytics(self) -> Dict:
        """
        Retrieve statistics about the indexed course catalog.
        
        Provides basic metrics for monitoring and UI display.
        
        Returns:
            Dictionary containing:
            - total_courses: Number of indexed courses
            - course_titles: List of all course titles
            
        Used By:
            - /stats endpoint for system monitoring
            - UI for displaying available courses
        """
        return {
            "total_courses": self.vector_store.get_course_count(),
            "course_titles": self.vector_store.get_existing_course_titles()
        }