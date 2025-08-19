# Infrastructure Module

The infrastructure module contains all external system integrations and technical implementations. This layer implements the interfaces defined in the core module.

## Structure

### persistence/
Data persistence implementations:

- **chroma_vector_store.py**: ChromaDB vector database implementation
- **in_memory_session_store.py**: In-memory session storage
- **course_repository.py**: Course data repository implementation
- **document_repository.py**: Document chunk repository implementation

### external_services/
External service integrations:

- **anthropic_ai_service.py**: Anthropic Claude AI integration
- **sentence_transformer_embedding.py**: Sentence transformer embedding service

### adapters/
Adapters for external systems (future expansion)

## Design Patterns

### Repository Pattern
Repositories provide an abstraction over data access, implementing the interfaces defined in core.

### Adapter Pattern
External services are wrapped in adapters that implement core interfaces, isolating the domain from external changes.

## Configuration

Infrastructure components are configured through dependency injection, receiving configuration from the application layer.

## Usage Example

```python
from src.infrastructure.persistence import ChromaVectorStore
from src.infrastructure.external_services import AnthropicAIService

# Create infrastructure components
vector_store = ChromaVectorStore(
    persist_path="./chroma_db",
    collection_name="courses"
)

ai_service = AnthropicAIService(
    api_key="your-key",
    model="claude-3"
)
```

## Testing

Infrastructure components should be tested with integration tests that verify:
- Database connections and operations
- External API interactions
- Error handling and resilience