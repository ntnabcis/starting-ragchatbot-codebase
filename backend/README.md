# Backend - Clean Architecture RAG System

This backend implements a Retrieval-Augmented Generation (RAG) system using clean architecture principles, SOLID design patterns, and industry best practices.

## Architecture Overview

The application follows clean architecture with clear separation of concerns:

```
src/
├── core/           # Interfaces & abstractions (no dependencies)
│   └── interfaces/ # Repository, service, and storage contracts
├── domain/         # Business logic (depends only on core)
│   ├── entities/   # Course, Lesson, DocumentChunk, Session
│   ├── services/   # DocumentProcessorService, TextChunkerService
│   └── value_objects/ # ChunkConfig, SearchParams, QueryResult
├── infrastructure/ # External integrations (implements core interfaces)
│   ├── persistence/    # ChromaVectorStore, repositories
│   └── external_services/ # AnthropicAIService, embeddings
├── application/    # Use cases & orchestration
│   ├── use_cases/  # QueryCourseUseCase, AddCourseUseCase
│   └── services/   # RAGOrchestrator, SearchService
├── presentation/   # API layer
│   ├── api/        # FastAPI routers
│   └── dependencies.py # Dependency injection container
└── shared/         # Configuration and utilities
    └── config.py   # AppConfig from environment
```

## Running the Application

### Development Mode
```bash
# From backend directory
uv run uvicorn app:app --reload --port 8000
```

### Production Mode
```bash
uv run uvicorn app:app --workers 4 --port 8000
```

## Database Management

Use the `manage_db.py` utility for database operations:

```bash
# Load documents (skips existing)
python manage_db.py

# Check database status
python manage_db.py --status

# Clear and reload all documents
python manage_db.py --clear

# Load from custom directory
python manage_db.py --path /path/to/docs
```

## Configuration

Create a `.env` file in the backend directory:

```env
# Required
ANTHROPIC_API_KEY=your-api-key-here

# Optional (with defaults)
ANTHROPIC_MODEL=claude-3-sonnet-20240229
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=800
CHUNK_OVERLAP=100
MAX_SEARCH_RESULTS=5
MAX_CONVERSATION_HISTORY=10
CHROMA_DB_PATH=./chroma_db
APP_NAME=Course Materials RAG System
APP_VERSION=2.0.0
DEBUG=false
```

## Key Features

### Clean Architecture Benefits
- **Testability**: Each component can be tested in isolation
- **Maintainability**: Clear boundaries and single responsibilities
- **Flexibility**: Easy to swap implementations (e.g., different AI providers)
- **Scalability**: Modular structure supports growth

### Performance Optimizations
- **Async Operations**: All I/O operations are asynchronous
- **Resource Management**: Sequential document processing prevents CPU spikes
- **Batch Processing**: Chunks saved in batches of 50
- **Background Loading**: Documents load after server startup
- **Embedded Database**: ChromaDB runs in-process (no separate server)

### Tool-Based Search
- Uses Anthropic's function calling for intelligent search
- `CourseSearchTool` defines search interface
- AI autonomously invokes search during response generation

### Dual Collection Strategy
ChromaDB manages two collections:
- **course_catalog**: Course metadata for fuzzy matching
- **course_content**: Document chunks for semantic search

## API Endpoints

### Core Endpoints
- `POST /api/query` - Process RAG queries
  - Request: `{"query": "string", "session_id": "optional"}`
  - Response: `{"answer": "string", "sources": ["string"], "session_id": "string"}`
- `GET /api/courses` - Get course statistics
- `GET /api/health` - Health check

### API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Design Patterns

### SOLID Principles
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Extend behavior via interfaces, not modification
- **Liskov Substitution**: Implementations interchangeable via interfaces
- **Interface Segregation**: Small, focused interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

### Architectural Patterns
- **Repository Pattern**: Abstract data access
- **Use Case Pattern**: Encapsulate business operations
- **Dependency Injection**: Loose coupling via DI container
- **Service Layer**: Orchestrate complex operations
- **Factory Pattern**: Create configured instances

## Module Dependencies

```
presentation → application → domain → core
     ↓             ↓           ↓
infrastructure ←──────────────┘
     ↓
  shared
```

## Development

### Project Structure
```
backend/
├── app.py              # ASGI application entry point
├── manage_db.py        # Database management utility
├── src/                # Source code (clean architecture)
├── chroma_db/          # Vector database storage
├── requirements.txt    # Python dependencies
└── .env               # Environment configuration
```

### Adding New Features

1. **Define interfaces** in `core/interfaces/`
2. **Create domain models** in `domain/entities/`
3. **Implement infrastructure** in `infrastructure/`
4. **Add use cases** in `application/use_cases/`
5. **Wire dependencies** in `presentation/dependencies.py`
6. **Create API routes** in `presentation/api/`

## Troubleshooting

### High CPU/Memory During Loading
- Documents process sequentially by design
- Use `manage_db.py` for manual control
- Check `presentation/dependencies.py` for resource limits

### Import Errors
- Ensure DTOs exported in `__init__.py` files
- Check entity exports in `domain/entities/__init__.py`
- Verify use case exports in `application/use_cases/__init__.py`

### Database Issues
- Run `python manage_db.py --status` to check state
- Use `python manage_db.py --clear` to reset
- Verify `.env` file has valid `ANTHROPIC_API_KEY`

## Testing

### Test Structure (Planned)
```
tests/
├── unit/           # Test individual components
├── integration/    # Test component interactions
└── e2e/           # Test complete flows
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/unit/test_document_processor.py
```

## Future Enhancements

- [ ] Comprehensive test suite
- [ ] Caching layer for embeddings
- [ ] WebSocket support for real-time queries
- [ ] Multi-tenant support
- [ ] Rate limiting and throttling
- [ ] Metrics and monitoring (Prometheus/Grafana)
- [ ] Docker containerization
- [ ] CI/CD pipeline

## License

[Specify your license here]