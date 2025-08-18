# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Course Materials RAG (Retrieval-Augmented Generation) System - a FastAPI-based web application that enables semantic search and AI-powered Q&A over course materials using ChromaDB for vector storage and Anthropic's Claude for response generation.

## Development Commands

### Running the Application
```bash
# Quick start with the provided script
./run.sh

# Or manually start the backend server
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Package Management
```bash
# Install/sync dependencies (using uv package manager)
uv sync

# Add new dependencies
uv add <package-name>
```

## Architecture Overview

### Core Components

The system follows a modular architecture with clear separation of concerns:

1. **RAG System** (`backend/rag_system.py`): Main orchestrator that coordinates all components - document processing, vector storage, AI generation, and session management.

2. **Vector Storage** (`backend/vector_store.py`): Manages ChromaDB collections for semantic search. Stores both course metadata and content chunks with embeddings using sentence-transformers.

3. **Document Processing** (`backend/document_processor.py`): Handles course document parsing, chunking strategy, and metadata extraction. Creates structured Course and Lesson objects from raw text files.

4. **AI Generation** (`backend/ai_generator.py`): Interfaces with Anthropic's Claude API for generating contextual responses based on retrieved course content.

5. **Session Management** (`backend/session_manager.py`): Maintains conversation history and context across user sessions.

6. **Search Tools** (`backend/search_tools.py`): Implements tool-based search functionality that can be extended with additional search capabilities.

### Data Flow

1. Course documents (`.txt` files in `docs/`) are processed into structured chunks
2. Chunks are embedded and stored in ChromaDB collections
3. User queries trigger semantic search to retrieve relevant chunks
4. Retrieved context is passed to Claude for response generation
5. Session history is maintained for contextual conversations

### API Structure

- FastAPI application (`backend/app.py`) serves both the API and static frontend files
- Main endpoints:
  - `POST /query` - Process user questions
  - `GET /stats` - Get course statistics
  - `POST /initialize` - Load course documents into the system
  - Static files served from `frontend/` directory

### Frontend

Simple vanilla JavaScript/HTML interface (`frontend/`) that communicates with the backend API for chat functionality.

## Environment Configuration

Required environment variable in `.env`:
```
ANTHROPIC_API_KEY=your_api_key_here
```

## Key Dependencies

- **FastAPI** & **Uvicorn**: Web framework and ASGI server
- **ChromaDB**: Vector database for semantic search
- **Sentence-Transformers**: For generating embeddings
- **Anthropic**: Claude AI integration
- **Python-dotenv**: Environment variable management