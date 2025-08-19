# Presentation Module

The presentation module handles all external communication with the application, including API endpoints, middleware, and dependency injection.

## Structure

### api/
REST API endpoints organized by domain:

- **query_router.py**: Query-related endpoints
- **course_router.py**: Course management endpoints  
- **health_router.py**: Health check endpoints

### middleware/
Cross-cutting concerns (future expansion):
- Authentication
- Logging
- Rate limiting

### dependencies.py
Dependency injection container that wires the entire application together.

## Key Components

### API Routers
FastAPI routers that:
- Define HTTP endpoints
- Validate input/output with Pydantic models
- Delegate to use cases
- Handle errors appropriately

### Dependency Injection
The `dependencies.py` module:
- Creates all application components
- Wires dependencies together
- Provides singleton instances
- Manages application lifecycle

## Design Principles

### Separation of Concerns
Presentation layer only handles:
- HTTP request/response mapping
- Input validation
- Error formatting
- No business logic

### Dependency Inversion
Controllers depend on use case abstractions, not concrete implementations.

## Usage Example

```python
from fastapi import FastAPI, Depends
from src.presentation.api import query_router
from src.presentation.dependencies import get_dependencies

app = FastAPI()
app.include_router(query_router)

# Dependencies are injected automatically
@app.on_event("startup")
async def startup():
    deps = get_dependencies()
    # Initialize resources
```

## Configuration

The presentation layer reads configuration from environment variables and passes it down through dependency injection.

## Error Handling

Consistent error responses:
- 400: Bad Request (validation errors)
- 404: Not Found
- 500: Internal Server Error

## Testing

Presentation layer testing:
- API integration tests
- Mock use cases
- Verify HTTP contracts