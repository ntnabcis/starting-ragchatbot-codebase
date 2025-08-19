# Architecture Documentation - RAG Chatbot System

## Overview

This document provides comprehensive documentation of the RAG Chatbot system's clean architecture implementation, including design decisions, module responsibilities, and troubleshooting guidance.

## Architecture Transformation

### Before (Monolithic)
```
backend/
├── app.py           # Monolithic application entry
├── config.py        # Configuration
├── models.py        # Data models
├── rag_system.py    # Main logic
├── vector_store.py  # Storage
├── ai_generator.py  # AI integration
├── document_processor.py
├── search_tools.py
└── session_manager.py
```
*Note: Original monolithic files have been removed. Only the refactored architecture remains.*

### After (Clean Architecture)
```
backend/
├── app.py          # New single entry point (imports from src/main.py)
├── manage_db.py    # Database management utility
└── src/
    ├── main.py     # FastAPI application factory
    ├── core/       # Abstractions & Interfaces (no dependencies)
    │   └── interfaces/
    │       ├── repository_interfaces.py  # Data persistence contracts
    │       ├── service_interfaces.py     # Business service contracts
    │       └── storage_interfaces.py     # Storage abstraction
    ├── domain/     # Business Logic (depends only on core)
    │   ├── entities/       # Course, Lesson, DocumentChunk, Session
    │   ├── value_objects/  # ChunkConfig, SearchParams, QueryResult
    │   └── services/       # DocumentProcessorService, TextChunkerService
    ├── infrastructure/     # External Systems
    │   ├── persistence/    # ChromaVectorStore, repositories
    │   └── external_services/  # AnthropicAIService, SentenceTransformerEmbedding
    ├── application/        # Use Cases & Orchestration
    │   ├── use_cases/      # QueryCourseUseCase, AddCourseUseCase, GetAnalyticsUseCase
    │   └── services/       # RAGOrchestrator, SearchService, CourseManagementService
    ├── presentation/       # API & Dependency Injection
    │   ├── api/            # query_router, course_router, health_router
    │   └── dependencies.py # Dependency injection container
    └── shared/
        └── config.py       # AppConfig from environment
```

## Key Architectural Decisions

### Tool-Based Search Pattern
The system uses Anthropic's function/tool calling capability:
- `CourseSearchTool` defines the search interface for the AI
- AI can autonomously invoke search during response generation
- Results are seamlessly integrated into the response context

### Dual Collection Strategy
ChromaDB manages two separate collections:
- **course_catalog**: Stores course metadata for fuzzy name matching
- **course_content**: Stores document chunks with embeddings for semantic search
This separation optimizes both metadata queries and content retrieval.

### Resource Management Strategy
To prevent system overload during document processing:
- Sequential processing instead of parallel (prevents CPU spikes)
- Batch saving of chunks (groups of 50)
- Background loading with delays
- Use of `run_in_executor` for blocking operations in async context

## Key Improvements

### 1. Separation of Concerns
Each module has a single, well-defined responsibility:
- **Core**: Defines contracts (interfaces)
- **Domain**: Contains business logic
- **Infrastructure**: Implements external integrations
- **Application**: Orchestrates use cases
- **Presentation**: Handles HTTP/API concerns

### 2. Dependency Inversion
- High-level modules don't depend on low-level modules
- Both depend on abstractions (interfaces)
- Implementations can be swapped without changing business logic

### 3. Testability
- Each component can be tested in isolation
- Dependencies are injected, making mocking easy
- Clear boundaries enable focused testing

### 4. Maintainability
- Changes are localized to specific modules
- New features can be added without modifying existing code
- Clear structure makes navigation easier

## Current State

### Running the Application
The refactored version is now the primary implementation:
```bash
# Quick start with script
./run.sh

# Manual start from backend directory
cd backend
uv run uvicorn app:app --reload --port 8000
```

### Database Management
```bash
cd backend
python manage_db.py           # Load documents (skip existing)
python manage_db.py --status  # Check database status
python manage_db.py --clear   # Clear and reload all documents
python manage_db.py --path /custom/path  # Load from custom directory
```

## Migration Complete

The refactoring has been fully implemented:
- Original monolithic files have been removed
- All functionality migrated to clean architecture
- API endpoints remain unchanged for backward compatibility
- Document loading optimized with resource management

## Module Responsibilities

### Core Module
- **Purpose**: Define contracts and abstractions
- **Dependencies**: None
- **Key Files**: Interface definitions

### Domain Module
- **Purpose**: Business logic and domain models
- **Dependencies**: Core interfaces only
- **Key Components**:
  - Entities (Course, Lesson, DocumentChunk, Session)
  - Value Objects (ChunkConfig, SearchParams, QueryResult)
  - Domain Services (DocumentProcessorService, TextChunkerService)

### Infrastructure Module
- **Purpose**: External system integrations
- **Dependencies**: Core interfaces, Domain models
- **Key Components**:
  - ChromaVectorStore (dual collections: course_catalog, course_content)
  - AnthropicAIService (Claude integration with tool support)
  - CourseRepository, DocumentRepository (repository implementations)
  - InMemorySessionStore (session management)
  - SentenceTransformerEmbeddingService (text embeddings)

### Application Module
- **Purpose**: Use case orchestration
- **Dependencies**: Core, Domain, Infrastructure
- **Key Components**:
  - Use Cases (QueryCourseUseCase, AddCourseUseCase, GetAnalyticsUseCase)
  - RAGOrchestrator (coordinates search, AI, and session management)
  - SearchService (semantic search with CourseSearchTool)
  - CourseManagementService (document loading and analytics)

### Presentation Module
- **Purpose**: API and dependency injection
- **Dependencies**: All layers
- **Key Components**:
  - FastAPI routers (query_router, course_router, health_router)
  - dependencies.py (singleton instances, resource management)
  - Middleware (CORS, TrustedHost)
  - Static file serving for frontend

## Benefits Achieved

### Immediate Benefits
- ✅ Clear code organization
- ✅ Reduced coupling
- ✅ Improved testability
- ✅ Better error handling
- ✅ Consistent patterns

### Long-term Benefits
- ✅ Easier to add new features
- ✅ Simpler to swap implementations
- ✅ Better team collaboration
- ✅ Reduced technical debt
- ✅ Improved performance (async/await)

## Best Practices Applied

### SOLID Principles
- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion

### Design Patterns
- Repository Pattern
- Use Case Pattern
- Dependency Injection
- Factory Pattern
- Service Layer Pattern

### Code Quality
- Type hints throughout all modules
- Comprehensive docstrings with parameter/return documentation
- Consistent naming conventions (snake_case, clear descriptive names)
- Error handling with graceful fallbacks
- Async/await for all I/O operations
- Pydantic models for request/response validation
- Clear separation between DTOs and domain models

## Testing Strategy

### Unit Tests
Test individual components:
```python
# Example: Testing domain service
def test_document_processor():
    config = ChunkConfig(800, 100)
    processor = DocumentProcessorService(config)
    # Test processing logic
```

### Integration Tests
Test component interactions:
```python
# Example: Testing repository with database
async def test_course_repository():
    repo = CourseRepository(vector_store)
    await repo.save_course(course_data)
    # Verify persistence
```

### End-to-End Tests
Test complete flows:
```python
# Example: Testing API endpoint
async def test_query_endpoint():
    response = await client.post("/api/query", json={...})
    assert response.status_code == 200
```

## Performance Improvements

- **Async Operations**: All I/O operations are async
- **Resource Management**: Sequential document processing prevents CPU spikes
- **Batch Processing**: Chunks saved in batches of 50
- **Background Loading**: Documents load asynchronously after startup
- **Embedded ChromaDB**: No separate server required
- **Session Limits**: History limited to 6 messages to manage memory

## Security Enhancements

- **Input Validation**: Pydantic models validate all inputs
- **Error Masking**: Internal errors not exposed to clients
- **Configuration**: Sensitive data in environment variables
- **Dependency Updates**: Latest library versions

## Monitoring & Observability

Ready for:
- Structured logging
- Metrics collection
- Distributed tracing
- Health checks
- Performance monitoring

## Implementation Status

### Completed ✅
- ✅ Clean architecture implementation
- ✅ Modular structure with clear boundaries
- ✅ Dependency injection container
- ✅ Comprehensive code documentation
- ✅ Resource management for CPU/memory optimization
- ✅ Database management utility (manage_db.py)
- ✅ Background document loading
- ✅ Tool-based search with Anthropic function calling

### Phase 2 (Planned)
- [ ] Comprehensive test suite
- [ ] CI/CD pipeline
- [ ] Docker containerization
- [ ] API versioning

### Phase 3 (Future)
- [ ] Microservices split
- [ ] Event-driven architecture
- [ ] Caching layer
- [ ] Rate limiting

## Key Files and Their Roles

### Entry Points
- `backend/app.py`: ASGI application entry point
- `backend/src/main.py`: FastAPI application factory and configuration
- `backend/manage_db.py`: Standalone database management utility

### Critical Configuration
- `backend/src/presentation/dependencies.py`: Wires the entire application
  - Creates singleton instances
  - Manages initialization order
  - Implements resource management fixes
  - Provides dependencies to API routes

### Core Business Logic
- `backend/src/application/services/rag_orchestrator.py`: Main query flow coordinator
- `backend/src/application/services/search_service.py`: Semantic search implementation
- `backend/src/domain/services/document_processor.py`: Document parsing logic

## Troubleshooting Guide

### Common Issues and Solutions

**High CPU/Memory During Document Loading**
- Solution implemented in `dependencies.py` with sequential processing
- Use `manage_db.py` for manual control over loading
- Documents process one at a time with delays

**Import Errors (MessageRole, QueryCourseRequest)**
- Ensure all DTOs exported in respective `__init__.py` files
- Check `domain/entities/__init__.py` exports all entities
- Check `application/use_cases/__init__.py` exports request/response classes

**"Failed to load courses" Error**
- Verify `.env` file exists with valid ANTHROPIC_API_KEY
- Check `docs/` directory contains `.txt` files in correct format
- Run `python manage_db.py --status` to verify database state
- Use `python manage_db.py --clear` to reset and reload

## Conclusion

This refactoring successfully transforms the codebase into a maintainable, scalable, and testable system following clean architecture principles and SOLID design patterns. The modular structure enables:

- **Easy Testing**: Each component can be tested in isolation
- **Flexible Extension**: New features added without modifying existing code
- **Implementation Swapping**: Different implementations can be plugged in via interfaces
- **Clear Boundaries**: Each layer has well-defined responsibilities
- **Performance Optimization**: Resource management prevents system overload

The architecture is production-ready with comprehensive documentation, error handling, and resource management strategies in place.