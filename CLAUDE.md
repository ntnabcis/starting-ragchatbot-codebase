# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Docker (Recommended)
- **Run with Docker**: `docker-compose up` (development with hot-reload) or `docker-compose up -d` (background)
- **Build images**: `docker-compose build --no-cache`
- **Stop services**: `docker-compose down`
- **View logs**: `docker-compose logs -f rag-backend`
- **Production mode**: `docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d`

### Local Development
- **Run the application**: `./run.sh` or `cd backend && uv run uvicorn app:app --reload --port 8000`
- **Install dependencies**: `uv sync`
- **Set up environment**: Copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY`

### Testing & Quality
- No test suite is currently configured. Consider implementing tests using pytest.
- No linting or type checking commands are configured. Consider adding ruff or similar tools.

## Architecture

This is a **Retrieval-Augmented Generation (RAG) system** for course materials.

### Core Components

**RAG System** (`backend/rag_system.py`): Main orchestrator that:
- Processes course documents into searchable chunks
- Manages vector storage with ChromaDB for semantic search
- Coordinates AI response generation using Claude
- Maintains conversation history across sessions
- Implements tool-based search for precise content retrieval

**API Layer** (`backend/app.py`): FastAPI application with:
- `/api/query`: Process queries with context-aware responses
- `/api/courses`: Return course catalog statistics
- Static file serving for frontend (handles both Docker and local paths)
- CORS and trusted host middleware for proxy compatibility

**Vector Storage** (`backend/vector_store.py`): ChromaDB implementation:
- Two collections: course metadata and content chunks
- Embedding model: all-MiniLM-L6-v2 for semantic similarity
- Configurable result limits and search parameters

**Document Processing** (`backend/document_processor.py`):
- Parses course documents (txt, pdf, docx formats)
- Chunks text with 800 char size, 100 char overlap
- Maintains course/lesson structure in metadata

**AI Generation** (`backend/ai_generator.py`):
- Anthropic Claude integration (claude-sonnet-4-20250514)
- Tool-based function calling for structured searches
- Conversation history support

### Data Models (`backend/models.py`)
- `Course`: Course metadata with lessons
- `Lesson`: Individual lesson with number and title
- `CourseChunk`: Text chunk with course/lesson references

### Docker Architecture
- Multi-stage production build (~200MB final image)
- Non-root user execution for security
- Volume persistence for ChromaDB data
- Development mode with hot-reload support
- Production mode with Nginx reverse proxy

### Data Flow
1. Documents loaded from `docs/` folder on startup
2. Text chunked and embedded into ChromaDB vectors
3. User queries trigger semantic similarity search
4. Tool-based search retrieves relevant chunks
5. Claude generates response using context
6. Session history maintained for follow-up questions

### Configuration
- `backend/config.py`: Core settings (chunk size, models, paths)
- `.env`: API keys and runtime configuration
- `docker-compose.yml`: Container orchestration
- ChromaDB persisted in volume or `./chroma_db` locally