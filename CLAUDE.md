# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Quick start using the provided shell script
chmod +x run.sh
./run.sh

# Manual start (from project root)
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Testing
```bash
# Run all tests with the test script
./run_tests.sh

# Run with coverage
./run_tests.sh -c

# Run specific test file or class
./run_tests.sh -t test_document_processor.py
./run_tests.sh -t TestChunkText

# Manual pytest execution (from backend/)
cd backend
uv run pytest tests/                                    # All tests
uv run pytest tests/ --cov=. --cov-report=term-missing # With coverage
uv run pytest tests/test_document_processor.py::TestChunkText::test_chunk_text_single_sentence  # Single test
```

### Dependency Management
```bash
# Install dependencies using uv package manager
uv sync

# Add runtime dependencies
uv add <package_name>

# Add dev dependencies
uv add --dev <package_name>
```

### Environment Setup
Create a `.env` file in the root directory with:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Architecture Overview

### System Design
This is a Retrieval-Augmented Generation (RAG) system built with:
- **FastAPI** backend serving both API endpoints and static frontend
- **ChromaDB** for vector storage and semantic search
- **Anthropic Claude** for AI generation
- **Sentence Transformers** for document embeddings

### Core Components

**backend/rag_system.py** (Main orchestrator)
- Coordinates document processing, vector storage, and AI generation
- Manages tool-based search through `ToolManager`
- Handles session management for conversation context

**backend/app.py** (FastAPI application)
- Serves API endpoints at `/api/query` and `/api/courses`
- Mounts frontend static files
- Loads initial documents from `docs/` folder on startup

**backend/vector_store.py**
- Manages ChromaDB collections for courses and content chunks
- Handles semantic search operations
- Stores course metadata and chunked content separately

**backend/ai_generator.py**
- Interfaces with Anthropic Claude API
- Implements tool-based search for course materials
- Manages conversation history in prompts

**backend/document_processor.py**
- Parses course documents into structured Course and Lesson objects
- Chunks content for vector storage with configurable size/overlap
- Generates unique IDs for tracking

**backend/search_tools.py**
- Implements `CourseSearchTool` for AI-driven search
- Manages tool definitions and execution
- Tracks sources from searches

### Data Flow
1. Documents in `docs/` folder are processed on startup
2. Text is chunked and embedded into ChromaDB collections
3. User queries trigger semantic search via AI tool calls
4. Claude generates responses using retrieved context
5. Session history is maintained for conversation continuity

### Document Processing
The `DocumentProcessor` expects course documents with this format:
```
Course Title: [title]
Course Link: [optional URL]
Course Instructor: [optional name]

Lesson 0: [lesson title]
Lesson Link: [optional URL]
[lesson content]

Lesson 1: [lesson title]
[lesson content]
```
- First line without "Course Title:" prefix is used as title fallback
- Lessons are identified by pattern "Lesson N:" (case-insensitive)
- Content is chunked with overlap for better context preservation
- Each chunk includes course title and lesson number for context

### Testing Strategy
- Unit tests in `backend/tests/` directory
- Test files follow `test_*.py` naming convention
- Tests organized in classes by functionality (e.g., `TestChunkText`, `TestProcessCourseDocument`)
- Fixtures and parameterized tests used to reduce duplication
- Current coverage: 99% for document_processor.py

### Key Configuration (backend/config.py)
- `CHUNK_SIZE`: 800 characters per chunk
- `CHUNK_OVERLAP`: 100 character overlap between chunks
- `MAX_RESULTS`: 5 search results per query
- `MAX_HISTORY`: 2 conversation exchanges remembered
- `EMBEDDING_MODEL`: all-MiniLM-L6-v2
- `ANTHROPIC_MODEL`: claude-sonnet-4-20250514