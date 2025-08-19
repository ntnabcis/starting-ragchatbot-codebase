"""
FastAPI application factory and configuration.

Assembles the complete RAG chatbot application with all middleware,
routers, and static file serving configured.
"""

import warnings
# Suppress multiprocessing resource tracker warnings in async context
warnings.filterwarnings("ignore", message="resource_tracker: There appear to be.*")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from .shared.config import AppConfig
from .presentation.dependencies import get_dependencies, load_initial_documents_safe
from .presentation.api import query_router, course_router, health_router


async def load_initial_documents_async():
    """
    Load course documents asynchronously after server startup.
    
    Delays execution to ensure server is fully initialized before
    intensive document processing begins.
    
    Error Handling:
        Catches and logs errors to prevent startup failure
        if documents are missing or corrupted.
    """
    import asyncio
    # Brief delay ensures server is ready for requests
    await asyncio.sleep(2)
    print("Starting background document loading...")
    try:
        await load_initial_documents_safe()
        print("Background document loading completed!")
    except Exception as e:
        print(f"Background document loading failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.
    
    Handles startup and shutdown operations including:
    - Background document loading on startup
    - Resource cleanup on shutdown
    
    Args:
        app: FastAPI application instance
        
    Yields:
        Control back to FastAPI after startup tasks
        
    Design Choice:
        Documents load asynchronously to prevent blocking
        the server startup and initial request handling.
    """
    print("Application starting...")
    
    # Schedule document loading without blocking startup
    try:
        import asyncio
        # Create background task for document processing
        asyncio.create_task(load_initial_documents_async())
        print("Document loading scheduled in background...")
    except Exception as e:
        print(f"Note: Document loading will be skipped: {e}")
    
    yield  # Application runs here
    
    print("Application shutting down...")


def create_app() -> FastAPI:
    """
    Factory function to create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application instance
        
    Configuration Steps:
        1. Load and validate environment configuration
        2. Initialize dependency injection container
        3. Create FastAPI app with lifecycle management
        4. Configure middleware stack
        5. Mount API routers
        6. Setup static file serving
        
    Raises:
        ValueError: If configuration validation fails
    """
    # Load configuration from environment
    config = AppConfig.from_env()
    config.validate()
    
    # Initialize dependency injection container
    get_dependencies()
    
    # Create FastAPI instance with configuration
    app = FastAPI(
        title=config.app_name,
        version=config.app_version,
        root_path="",
        lifespan=lifespan  # Lifecycle manager for startup/shutdown
    )
    
    # Security middleware for host validation
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure for production environment
    )
    
    # CORS middleware for cross-origin requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"]
    )
    
    # Mount API routers
    app.include_router(query_router)  # Document query endpoints
    app.include_router(course_router)  # Course management endpoints
    app.include_router(health_router)  # Health check endpoints
    
    # Serve frontend static files
    # Note: Mounted last to avoid intercepting API routes
    app.mount("/", StaticFiles(directory="../frontend", html=True), name="static")
    
    return app


# Create application instance for ASGI server
app = create_app()