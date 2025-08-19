"""
Main application entry point for the RAG chatbot system.

This module serves as the primary entry point for the FastAPI application,
importing the configured app instance from the modular architecture.

Usage:
    Development: uvicorn app:app --reload --port 8000
    Production: uvicorn app:app --workers 4 --port 8000
    
Architecture:
    Delegates to src.main which assembles the application using
    dependency injection and clean architecture principles.
    
Key Features:
    - RESTful API for document queries
    - Course management endpoints
    - Static file serving for frontend
    - WebSocket support for real-time features
"""

from src.main import app

# Export app instance for ASGI server
__all__ = ['app']