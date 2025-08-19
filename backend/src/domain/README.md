# Domain Module

The domain module contains the core business logic, entities, and domain services. This module depends only on the core interfaces and represents the heart of the application's business rules.

## Purpose

The domain module encapsulates:
- Business entities and their behaviors
- Domain services for complex business operations
- Value objects for domain concepts
- Business rules and validations

## Structure

```
domain/
├── entities/       # Business entities with behavior
│   ├── __init__.py
│   ├── course.py       # Course aggregate root
│   ├── lesson.py       # Lesson entity
│   ├── document_chunk.py  # Document chunk entity
│   └── session.py      # Conversation session entity
├── services/       # Domain services
│   ├── __init__.py
│   ├── document_processor.py  # Document parsing logic
│   └── text_chunker.py        # Text chunking algorithms
└── value_objects/  # Immutable domain concepts
    ├── __init__.py
    ├── chunk_config.py    # Chunking configuration
    ├── query_result.py    # Query result structure
    └── search_params.py   # Search parameters
```

## Key Components

### Entities (`entities/`)

**Course** (`course.py`)
- Aggregate root for course management
- Properties: `title`, `instructor`, `lessons`, `created_at`, `updated_at`
- Methods: `add_lesson()`, `get_lesson()`, `to_dict()`, `from_dict()`
- Natural key: Course title

**Lesson** (`lesson.py`)
- Represents individual course lessons
- Properties: `lesson_number`, `title`, `lesson_link`
- Value object within Course aggregate

**DocumentChunk** (`document_chunk.py`)
- Represents processed text chunks for vector storage
- Properties: `id`, `content`, `metadata`, `embedding`
- Includes course and lesson context

**Session** (`session.py`)
- Manages conversation state
- Properties: `session_id`, `messages`, `created_at`
- Methods: `add_message()`, `get_history()`, `clear()`

### Domain Services (`services/`)

**DocumentProcessorService** (`document_processor.py`)
- Parses course documents into structured data
- Extracts metadata (title, instructor, lessons)
- Identifies lesson boundaries
- Returns: `(Course, List[DocumentChunk])`

**TextChunkerService** (`text_chunker.py`)
- Implements text chunking algorithms
- Configurable chunk size and overlap
- Maintains context across chunk boundaries
- Handles special cases (code blocks, lists)

### Value Objects (`value_objects/`)

**ChunkConfig** (`chunk_config.py`)
- Immutable configuration for chunking
- Properties: `chunk_size` (default: 800), `chunk_overlap` (default: 100)

**SearchParams** (`search_params.py`)
- Search operation parameters
- Properties: `query`, `course_name`, `lesson_number`, `limit`

**QueryResult** (`query_result.py`)
- Structured query response
- Properties: `answer`, `sources`, `confidence`, `metadata`

## Business Rules

### Course Management
1. Course titles must be unique (natural key)
2. Lessons automatically sorted by lesson_number
3. Timestamps updated on modifications

### Document Processing
1. Documents must follow the expected format
2. Each lesson creates multiple chunks with overlap
3. Metadata preserved for context retrieval

### Text Chunking
1. Chunks respect sentence boundaries when possible
2. Overlap ensures context continuity
3. Maximum chunk size enforced for embedding limits

## Usage Examples

### Creating Entities
```python
from src.domain.entities import Course, Lesson

course = Course(
    title="Machine Learning Fundamentals",
    instructor="Dr. Smith"
)
lesson = Lesson(lesson_number=1, title="Introduction to ML")
course.add_lesson(lesson)
```

### Using Domain Services
```python
from src.domain.services import DocumentProcessorService
from src.domain.value_objects import ChunkConfig

config = ChunkConfig(chunk_size=800, chunk_overlap=100)
processor = DocumentProcessorService(config)
course, chunks = await processor.process_document(file_path)
```

### Working with Value Objects
```python
from src.domain.value_objects import SearchParams

params = SearchParams(
    query="What is gradient descent?",
    course_name="Machine Learning",
    limit=5
)
```

## Design Patterns

### Domain-Driven Design
- **Aggregate Root**: Course serves as aggregate root
- **Entities**: Have identity and lifecycle
- **Value Objects**: Immutable, compared by value
- **Domain Services**: Encapsulate domain logic

### Business Logic Encapsulation
- Entities contain their own behavior
- Validation happens at domain level
- Complex operations in domain services

## Dependencies

**Allowed Dependencies:**
- Core interfaces only
- Python standard library
- Domain module internal components

**NOT Allowed:**
- Infrastructure implementations
- External frameworks
- Database libraries
- Web frameworks

## Testing

Domain components are highly testable:
```python
def test_course_add_lesson():
    course = Course(title="Test Course")
    lesson = Lesson(lesson_number=1, title="Lesson 1")
    course.add_lesson(lesson)
    assert course.lesson_count == 1
    assert course.get_lesson(1) == lesson
```

## Best Practices

1. **Keep domain pure**: No infrastructure concerns
2. **Rich domain models**: Behavior with data
3. **Immutable value objects**: Prevent unexpected changes
4. **Clear boundaries**: Separate domain from application logic
5. **Business language**: Use domain terminology