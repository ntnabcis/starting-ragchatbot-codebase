"""
Fixed dependency injection with proper resource management.
This version prevents CPU/memory spikes during initialization.
"""

from typing import Dict, Any, Optional
from pathlib import Path
import asyncio
import logging

from ..shared.config import AppConfig
from ..domain.value_objects import ChunkConfig

# Use lazy imports to reduce startup overhead
_dependencies: Optional[Dict[str, Any]] = None
_lock = asyncio.Lock()

logger = logging.getLogger(__name__)


def initialize_dependencies_sync(config: AppConfig) -> Dict[str, Any]:
    """
    Synchronous initialization of dependencies.
    This avoids async complexity during startup.
    """
    
    # Create chunk config
    chunk_config = ChunkConfig(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap
    )
    
    # Import heavy modules only when needed
    from ..infrastructure.persistence import (
        ChromaVectorStore,
        InMemorySessionStore,
        CourseRepository,
        DocumentRepository
    )
    
    from ..infrastructure.external_services import (
        AnthropicAIService,
        SentenceTransformerEmbeddingService
    )
    
    from ..application.services import (
        SearchService,
        RAGOrchestrator,
        CourseManagementService
    )
    
    from ..application.use_cases import (
        QueryCourseUseCase,
        AddCourseUseCase,
        GetAnalyticsUseCase
    )
    
    # Create vector stores with single shared client
    try:
        # Use a single ChromaDB client for both collections
        course_vector_store = ChromaVectorStore(
            persist_path=config.chroma_db_path,
            collection_name="course_catalog",
            embedding_model=config.embedding_model
        )
        
        content_vector_store = ChromaVectorStore(
            persist_path=config.chroma_db_path,
            collection_name="course_content",
            embedding_model=config.embedding_model
        )
    except Exception as e:
        logger.error(f"Failed to initialize vector stores: {e}")
        # Create in-memory fallback if ChromaDB fails
        raise
    
    # Create repositories
    course_repository = CourseRepository(course_vector_store)
    document_repository = DocumentRepository(content_vector_store)
    session_repository = InMemorySessionStore(config.max_conversation_history)
    
    # Create services (lazy initialization of embedding model)
    embedding_service = None  # Will be created on first use
    ai_service = AnthropicAIService(config.anthropic_api_key, config.anthropic_model)
    
    # Create application services
    search_service = SearchService(document_repository, course_repository)
    rag_orchestrator = RAGOrchestrator(search_service, ai_service, session_repository)
    course_management_service = CourseManagementService(
        course_repository, 
        document_repository, 
        chunk_config
    )
    
    # Create use cases
    query_use_case = QueryCourseUseCase(rag_orchestrator)
    add_course_use_case = AddCourseUseCase(course_management_service)
    analytics_use_case = GetAnalyticsUseCase(course_management_service)
    
    return {
        'config': config,
        'chunk_config': chunk_config,
        'course_repository': course_repository,
        'document_repository': document_repository,
        'session_repository': session_repository,
        'embedding_service': embedding_service,
        'ai_service': ai_service,
        'search_service': search_service,
        'rag_orchestrator': rag_orchestrator,
        'course_management_service': course_management_service,
        'query_use_case': query_use_case,
        'add_course_use_case': add_course_use_case,
        'analytics_use_case': analytics_use_case
    }


def get_dependencies() -> Dict[str, Any]:
    """Get or create dependencies singleton."""
    global _dependencies
    
    if _dependencies is None:
        config = AppConfig.from_env()
        config.validate()
        _dependencies = initialize_dependencies_sync(config)
    
    return _dependencies


async def load_initial_documents_safe(docs_path: str = "../docs") -> None:
    """
    Safe document loading that doesn't spike CPU/memory.
    Processes documents sequentially instead of in parallel.
    """
    deps = get_dependencies()
    course_service = deps['course_management_service']
    
    path = Path(docs_path)
    if not path.exists():
        logger.warning(f"Documents directory not found: {docs_path}")
        return
    
    print(f"Loading documents from {docs_path}...")
    
    try:
        # Get list of files to process
        txt_files = list(path.glob("*.txt"))
        if not txt_files:
            print("No documents found to load")
            return
        
        print(f"Found {len(txt_files)} document(s) to process")
        
        # Check existing courses first to avoid reprocessing
        existing = await course_service.course_repo.get_all_courses()
        existing_titles = {course.title for course in existing}
        
        if len(existing_titles) >= len(txt_files):
            print(f"Documents already loaded ({len(existing_titles)} courses in database)")
            return
        
        # Process documents one at a time to avoid resource spike
        total_courses = 0
        total_chunks = 0
        
        for file_path in txt_files:
            try:
                # Add small delay between files to prevent resource spike
                await asyncio.sleep(0.1)
                
                # Process single document
                from ..domain.services import DocumentProcessorService
                processor = DocumentProcessorService(deps['chunk_config'])
                
                # Run processing in thread pool
                loop = asyncio.get_event_loop()
                course, chunks = await loop.run_in_executor(
                    None,
                    processor.process_course_document,
                    file_path
                )
                
                if course.title in existing_titles:
                    print(f"  ✓ {course.title} (already exists)")
                    continue
                
                # Save to database
                from ..core.interfaces.repository_interfaces import CourseData
                course_data = CourseData(
                    title=course.title,
                    course_link=course.course_link,
                    instructor=course.instructor,
                    lessons=[lesson.to_dict() for lesson in course.lessons]
                )
                
                await course_service.course_repo.save_course(course_data)
                
                # Save chunks in batches to avoid memory issues
                chunk_batch = []
                for chunk in chunks:
                    chunk_batch.append({
                        'id': chunk.id,
                        'content': chunk.content,
                        'course_title': chunk.course_title,
                        'lesson_number': chunk.lesson_number,
                        'chunk_index': chunk.chunk_index
                    })
                    
                    # Save every 50 chunks
                    if len(chunk_batch) >= 50:
                        await course_service.document_repo.save_document_chunks(chunk_batch)
                        chunk_batch = []
                        await asyncio.sleep(0.05)  # Small delay to prevent spike
                
                # Save remaining chunks
                if chunk_batch:
                    await course_service.document_repo.save_document_chunks(chunk_batch)
                
                total_courses += 1
                total_chunks += len(chunks)
                existing_titles.add(course.title)
                
                print(f"  ✓ {course.title} ({len(chunks)} chunks)")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {e}")
                print(f"  ✗ {file_path.name}: {e}")
        
        print(f"Loaded {total_courses} courses with {total_chunks} chunks")
        
    except Exception as e:
        logger.error(f"Error loading documents: {e}")
        print(f"Error loading documents: {e}")