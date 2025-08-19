# Application Module

The application module orchestrates the business logic by coordinating between domain and infrastructure layers. It implements use cases and application services.

## Structure

### use_cases/
Application use cases that represent user actions:

- **query_course_use_case.py**: Handle course content queries
- **add_course_use_case.py**: Add new courses to the system
- **get_analytics_use_case.py**: Retrieve system analytics

### services/
Application services that coordinate complex operations:

- **search_service.py**: Coordinates search operations across repositories
- **rag_orchestrator.py**: Orchestrates RAG pipeline (search + AI generation)
- **course_management_service.py**: Manages course lifecycle and operations

### dto/
Data Transfer Objects for application boundaries (future expansion)

## Design Patterns

### Use Case Pattern
Each use case represents a single user action with:
- Request object (input)
- Response object (output)
- Execute method (business logic)

### Service Layer
Services coordinate multiple domain operations and infrastructure components.

## Key Concepts

### Orchestration
The RAGOrchestrator coordinates:
1. Search for relevant content
2. Build context from results
3. Generate AI response
4. Manage conversation history

### Transaction Boundaries
Use cases define transaction boundaries, ensuring consistency.

## Usage Example

```python
from src.application.use_cases import QueryCourseUseCase, QueryCourseRequest

# Create and execute use case
use_case = QueryCourseUseCase(rag_orchestrator)
request = QueryCourseRequest(
    query="What is machine learning?",
    session_id="session_123"
)
response = await use_case.execute(request)
```

## Testing

Application layer should be tested with:
- Unit tests for use cases
- Mock dependencies from infrastructure
- Verify orchestration logic