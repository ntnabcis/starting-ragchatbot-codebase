# Core Module

The core module defines the fundamental abstractions and interfaces that establish the contracts for the entire application. This module has **zero dependencies** on external libraries, frameworks, or other modules.

## Purpose

The core module serves as the foundation of the clean architecture by:
- Defining abstract interfaces that all other modules implement
- Establishing contracts without implementation details
- Ensuring dependency inversion principle is maintained
- Providing a stable foundation that rarely changes

## Structure

```
core/
├── interfaces/
│   ├── __init__.py
│   ├── repository_interfaces.py  # Data persistence contracts
│   ├── service_interfaces.py     # Business service contracts
│   └── storage_interfaces.py     # Storage abstraction contracts
├── exceptions/  # (if needed) Custom exception definitions
└── constants/   # (if needed) Application constants
```

## Key Interfaces

### Repository Interfaces (`repository_interfaces.py`)

**Data Transfer Objects:**
- `CourseData`: Lightweight course structure for repository operations
- `SessionData`: Conversation session data structure

**Repository Contracts:**
- `ICourseRepository`: Course metadata persistence
  - `get_course_by_title()`, `get_all_courses()`, `save_course()`
- `IDocumentRepository`: Document chunk persistence
  - `save_document_chunks()`, `get_chunks_by_course()`, `search_chunks()`
- `ISessionRepository`: Session management
  - `create_session()`, `get_session()`, `save_message()`, `get_session_history()`

### Service Interfaces (`service_interfaces.py`)

**Business Service Contracts:**
- `IDocumentProcessor`: Document parsing and chunking operations
  - `process_document()`, `chunk_text()`
- `ISearchService`: Semantic and metadata search
  - `search()`, `get_similar_courses()`
- `IAIService`: AI language model integration
  - `generate_response()`, `set_system_prompt()`
- `IEmbeddingService`: Text embedding generation
  - `generate_embedding()`, `generate_embeddings_batch()`

### Storage Interfaces (`storage_interfaces.py`)

**Storage Abstraction:**
- `IVectorStore`: Vector database operations
  - `add_documents()`, `search()`, `delete()`, `clear_collection()`
- `IDocumentStore`: Document storage operations (if separate from vector store)

## Design Principles

### 1. Dependency Inversion
- High-level modules depend on these abstractions
- Low-level modules implement these abstractions
- No direct dependencies between business logic and infrastructure

### 2. Interface Segregation
- Small, focused interfaces
- Clients depend only on methods they use
- Avoid "fat" interfaces with unnecessary methods

### 3. Stability
- Interfaces change rarely
- Implementation details hidden behind contracts
- Breaking changes minimized through careful design

## Usage Examples

### Defining Dependencies
```python
from src.core.interfaces.repository_interfaces import ICourseRepository
from src.core.interfaces.service_interfaces import IAIService

class MyService:
    def __init__(self, repo: ICourseRepository, ai: IAIService):
        # Depend on abstractions, not concrete implementations
        self.repo = repo
        self.ai = ai
```

### Implementing Interfaces
```python
from src.core.interfaces.repository_interfaces import ICourseRepository

class ChromaCourseRepository(ICourseRepository):
    async def get_course_by_title(self, title: str):
        # Concrete implementation
        pass
```

## Benefits

1. **Testability**: Easy to mock interfaces for testing
2. **Flexibility**: Swap implementations without changing business logic
3. **Clarity**: Clear contracts make the system easier to understand
4. **Maintainability**: Changes isolated to implementations
5. **Documentation**: Interfaces serve as living documentation

## Guidelines

### When to Add New Interfaces
- When introducing a new external dependency
- When defining a new business capability
- When abstracting complex operations

### Interface Design Best Practices
- Keep interfaces small and focused
- Use clear, descriptive method names
- Include comprehensive docstrings
- Define return types explicitly
- Consider async/await for I/O operations

## Dependencies

**This module has NO dependencies on:**
- External libraries
- Framework code
- Other application modules
- Implementation details

This independence ensures the core remains stable and testable.