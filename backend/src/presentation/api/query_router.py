"""
Query processing API endpoints.

Provides REST API routes for RAG-based document querying.
Handles user questions, context retrieval, and AI-generated responses.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional

from ...application.use_cases import QueryCourseUseCase, QueryCourseRequest


class QueryRequest(BaseModel):
    """
    Request model for document query endpoint.
    
    Attributes:
        query: User's question or search query
        session_id: Optional session for conversation continuity
    """
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """
    Response model for query results.
    
    Attributes:
        answer: AI-generated response to the query
        sources: List of source document references used
        session_id: Session identifier for follow-up queries
    """
    answer: str
    sources: List[str]
    session_id: str


# Initialize router with API prefix and OpenAPI tags
query_router = APIRouter(prefix="/api", tags=["queries"])


def get_query_use_case() -> QueryCourseUseCase:
    """
    Dependency injection function for query use case.
    
    Returns:
        QueryCourseUseCase: Configured query processing use case
        
    Note:
        Lazy import prevents circular dependencies during module loading.
    """
    from ..dependencies import get_dependencies
    deps = get_dependencies()
    return deps['query_use_case']


@query_router.post("/query", response_model=QueryResponse)
async def query_documents(
    request: QueryRequest,
    use_case: QueryCourseUseCase = Depends(get_query_use_case)
):
    """
    Process user query using RAG system.
    
    Performs semantic search on course documents and generates
    contextually-aware responses using AI.
    
    Args:
        request: Query request containing question and optional session
        use_case: Injected query processing use case
        
    Returns:
        QueryResponse: AI-generated answer with source references
        
    Raises:
        HTTPException: 500 status on query processing failure
        
    API Usage:
        POST /api/query
        Body: {"query": "What is machine learning?", "session_id": "abc123"}
        Returns: {"answer": "...", "sources": [...], "session_id": "abc123"}
        
    Implementation Flow:
        1. Convert API request to use case request
        2. Execute RAG pipeline (search, retrieve, generate)
        3. Transform use case response to API response
        4. Maintain session for conversation continuity
    """
    try:
        # Transform API request to use case request format
        uc_request = QueryCourseRequest(
            query=request.query,
            session_id=request.session_id
        )
        
        # Execute RAG pipeline through use case
        response = await use_case.execute(uc_request)
        
        # Handle use case errors gracefully
        if not response.success:
            raise HTTPException(status_code=500, detail=response.error)
        
        # Transform use case response to API response model
        return QueryResponse(
            answer=response.answer,
            sources=response.sources,
            session_id=response.session_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
    except Exception as e:
        # Wrap unexpected errors in 500 response
        raise HTTPException(status_code=500, detail=str(e))