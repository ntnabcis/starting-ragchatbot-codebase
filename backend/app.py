"""
FastAPI application for the Course Materials RAG System.

This module implements the REST API interface for the RAG system, providing
endpoints for querying course materials and retrieving system statistics.
It also serves the static frontend files and handles CORS for cross-origin
requests in development.
"""

import warnings
# Suppress ChromaDB multiprocessing warnings that are not relevant
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os

from config import config
from rag_system import RAGSystem

# Initialize FastAPI application with metadata
app = FastAPI(
    title="Course Materials RAG System",
    description="AI-powered Q&A system for course content",
    version="1.0.0",
    root_path=""  # For proxy compatibility
)

# Configure trusted host middleware
# Allows all hosts for development flexibility
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure specific hosts in production
)

# Configure CORS for frontend-backend communication
# Permissive settings for development - restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend origin
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # All HTTP methods
    allow_headers=["*"],  # All headers
    expose_headers=["*"],  # Make all headers visible to frontend
)

# Initialize RAG system with configuration
# Single global instance for all requests
rag_system = RAGSystem(config)

# API Request/Response Models

class QueryRequest(BaseModel):
    """
    Request model for course content queries.
    
    Attributes:
        query: User's question about course materials
        session_id: Optional session for conversation continuity
    """
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """
    Response model for query results.
    
    Attributes:
        answer: AI-generated response to the query
        sources: List of course/lesson references used
        session_id: Session identifier for follow-up questions
    """
    answer: str
    sources: List[str]
    session_id: str


class CourseStats(BaseModel):
    """
    Response model for system statistics.
    
    Attributes:
        total_courses: Number of indexed courses
        course_titles: List of available course names
    """
    total_courses: int
    course_titles: List[str]

# API Endpoints

@app.post("/api/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Process a user query about course materials.
    
    This endpoint handles the main Q&A functionality:
    1. Creates or retrieves a conversation session
    2. Processes the query through the RAG pipeline
    3. Returns AI response with source citations
    
    Args:
        request: QueryRequest with question and optional session
        
    Returns:
        QueryResponse with answer, sources, and session ID
        
    Raises:
        HTTPException: 500 on processing errors
    """
    try:
        # Ensure session exists for conversation tracking
        session_id = request.session_id
        if not session_id:
            session_id = rag_system.session_manager.create_session()
        
        # Execute RAG pipeline: search -> generate -> respond
        answer, sources = rag_system.query(request.query, session_id)
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            session_id=session_id
        )
    except Exception as e:
        # Log error and return user-friendly message
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/courses", response_model=CourseStats)
async def get_course_stats():
    """
    Retrieve statistics about indexed courses.
    
    Provides metadata about the course catalog for UI display
    and system monitoring.
    
    Returns:
        CourseStats with course count and titles
        
    Raises:
        HTTPException: 500 on retrieval errors
    """
    try:
        analytics = rag_system.get_course_analytics()
        return CourseStats(
            total_courses=analytics["total_courses"],
            course_titles=analytics["course_titles"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    """
    Initialize the system on application startup.
    
    Automatically loads course documents from the docs folder
    if it exists. Uses incremental loading to preserve any
    existing data in the vector store.
    
    Side Effects:
        - Indexes all documents in ../docs folder
        - Prints loading statistics to console
    """
    docs_path = "../docs"
    if os.path.exists(docs_path):
        print("Loading initial documents...")
        try:
            # Incremental load - preserves existing data
            courses, chunks = rag_system.add_course_folder(docs_path, clear_existing=False)
            print(f"Loaded {courses} courses with {chunks} chunks")
        except Exception as e:
            print(f"Error loading documents: {e}")

# Static File Serving

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from pathlib import Path


class DevStaticFiles(StaticFiles):
    """
    Custom static file handler for development.
    
    Adds no-cache headers to prevent browser caching during
    development, ensuring changes are immediately visible.
    """
    
    async def get_response(self, path: str, scope):
        """
        Override to add cache-busting headers.
        
        Args:
            path: Requested file path
            scope: ASGI scope
            
        Returns:
            FileResponse with no-cache headers
        """
        response = await super().get_response(path, scope)
        if isinstance(response, FileResponse):
            # Prevent all caching in development
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


# Mount frontend as root to serve SPA
# html=True enables serving index.html for routes
app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")