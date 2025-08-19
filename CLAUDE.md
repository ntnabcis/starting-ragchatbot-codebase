# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Retrieval-Augmented Generation (RAG) system for intelligent querying of course materials. Built with clean architecture using FastAPI, ChromaDB for vector storage, and Anthropic Claude for AI responses. The system performs semantic search on course documents and generates context-aware educational responses.

## Development Commands

### Running the Application
```bash
# Quick start with shell script
./run.sh

# Manual start
cd backend
uv run uvicorn app:app --reload --port 8000
```

### Dependency Management
```bash
# Install dependencies
uv sync

# Add new dependency
uv add [package-name]
```

### Database Management
```bash
cd backend
python manage_db.py           # Load documents (skip existing)
python manage_db.py --status  # Check database status
python manage_db.py --clear   # Clear and reload all documents
python manage_db.py --path /custom/path  # Load from custom directory
```

### Environment Setup
Ensure `backend/.env` file exists with:
```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Architecture

### Clean Architecture Layers

The system follows clean architecture with strict dependency rules:

```
backend/src/
├── core/           # Interfaces & abstractions (no dependencies)
│   └── interfaces/
│       ├── repository_interfaces.py  # Data persistence contracts
│       ├── service_interfaces.py     # Business service contracts
│       └── storage_interfaces.py     # Storage abstraction
├── domain/         # Business logic (depends only on core)
│   ├── entities/   # Course, Lesson, DocumentChunk, Session
│   ├── services/   # DocumentProcessorService, TextChunkerService
│   └── value_objects/  # ChunkConfig, SearchParams, QueryResult
├── infrastructure/ # External integrations (implements core interfaces)
│   ├── persistence/     # ChromaVectorStore, repositories
│   └── external_services/  # AnthropicAIService, embeddings
├── application/    # Use cases & orchestration
│   ├── use_cases/  # QueryCourseUseCase, AddCourseUseCase
│   └── services/   # RAGOrchestrator, SearchService
└── presentation/   # API layer
    ├── api/        # FastAPI routers
    └── dependencies.py  # Dependency injection container
```

### Core Components Flow

**Query Processing Pipeline:**
1. **API Router** (`presentation/api/query_router.py`) receives POST /api/query
2. **QueryCourseUseCase** (`application/use_cases/`) validates request
3. **RAGOrchestrator** (`application/services/`) coordinates:
   - Calls **SearchService** for semantic search via CourseSearchTool
   - Retrieves relevant chunks from **ChromaVectorStore**
   - Invokes **AnthropicAIService** with context
   - Manages **SessionManager** for conversation history
4. Response returned with answer and source references

**Document Processing Pipeline:**
1. **CourseManagementService** (`application/services/`) orchestrates loading
2. **DocumentProcessorService** (`domain/services/`) parses course files:
   - Extracts metadata (title, instructor, lessons)
   - Identifies lesson boundaries
3. **TextChunkerService** creates overlapping chunks (800 chars, 100 overlap)
4. **ChromaVectorStore** stores in dual collections:
   - `course_catalog`: Course metadata for fuzzy matching
   - `course_content`: Document chunks with embeddings

### Tool-Based Search Architecture

The system uses Anthropic's tool/function calling pattern:
- **CourseSearchTool** (`application/services/search_tools.py`) defines search interface
- AI can invoke search tool to find relevant content
- Results integrated into response generation

### Dependency Injection

`presentation/dependencies.py` manages all component wiring:
- Creates singleton instances
- Handles initialization order
- Provides resource management (sequential processing, batch saves)
- Prevents CPU/memory spikes during document loading

### Key Design Patterns

- **Repository Pattern**: Abstract data access behind interfaces
- **Use Case Pattern**: Encapsulate business operations
- **Dependency Inversion**: High-level modules depend on abstractions
- **Service Layer**: Orchestrate complex operations
- **Factory Pattern**: Create configured service instances

## API Structure

### Endpoints
- `POST /api/query`: Process RAG queries
- `GET /api/courses`: Get course statistics
- `GET /api/health`: Health check
- Static files served from `frontend/` directory

### Data Flow
1. Documents processed into Course objects and CourseChunks
2. Metadata and chunks stored in separate ChromaDB collections
3. Queries trigger semantic search via CourseSearchTool
4. AI generates responses using retrieved context
5. Session history maintains conversation continuity

## Document Format

Course documents in `docs/` should follow:
```
Course Title: [Title]
Course Link: [URL]
Course Instructor: [Name]

Lesson 0: [Title]
Lesson Link: [URL]
[Content...]

Lesson 1: [Title]
[Content...]
```

## Performance & Resource Management

### Optimizations
- Documents processed sequentially to prevent CPU spikes
- Chunks saved in batches of 50
- Async operations with `run_in_executor` for blocking code
- ChromaDB runs embedded (no separate server)
- Session history limited to last 6 messages

### Common Issues

**High CPU/Memory During Loading:**
- Use `manage_db.py` for manual document loading control
- Documents process one at a time with delays

**Import Errors:**
- Ensure request/response classes exported in `__init__.py` files
- Check `MessageRole` exported from `domain/entities/__init__.py`

## SOLID Principles Applied

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Extend behavior via interfaces, not modification
- **Liskov Substitution**: Implementations interchangeable via interfaces
- **Interface Segregation**: Small, focused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions